require('dotenv').config();

const crypto = require('crypto');
const path = require('path');

const express = require('express');
const cors = require('cors');

const sheets = require('./googleSheets');

const app = express();
const PORT = process.env.PORT || 3000;
const BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const SPREADSHEET_ID = process.env.SPREADSHEET_ID || '1whENuiefsDr1I5GvvzRiwjbGQUhYk8szo7F6LmDVTmI';
const SHEET_NAME = process.env.SHEET_NAME || 'students';
const ADMIN_TELEGRAM_IDS = new Set(
    String(process.env.ADMIN_TELEGRAM_IDS || '')
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean)
);
const ALLOWED_UNIVERSITIES = new Set(['БГУ', 'ИГУ']);
const activeRequests = new Set();

app.use(cors());
app.use(express.json());
app.use(express.static(__dirname));

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

app.get('/admin', (req, res) => {
    res.sendFile(path.join(__dirname, 'admin.html'));
});

app.get('/api/test', (req, res) => {
    res.json({
        message: 'Сервер работает',
        spreadsheetId: SPREADSHEET_ID,
        sheetName: SHEET_NAME,
        adminConfigured: ADMIN_TELEGRAM_IDS.size > 0
    });
});

app.get('/api/google-check', async (req, res) => {
    try {
        const meta = await sheets.spreadsheets.get({
            spreadsheetId: SPREADSHEET_ID,
            fields: 'spreadsheetId,properties.title'
        });

        const response = await sheets.spreadsheets.values.get({
            spreadsheetId: SPREADSHEET_ID,
            range: `${SHEET_NAME}!A1:F1`,
        });

        res.json({
            ok: true,
            spreadsheetId: meta.data.spreadsheetId,
            spreadsheetTitle: meta.data.properties?.title || null,
            sheetName: SHEET_NAME,
            headerRow: response.data.values?.[0] || []
        });
    } catch (error) {
        const details = getGoogleErrorMessage(error);
        console.error('google-check error:', details, error);
        res.status(500).json({ ok: false, message: details });
    }
});

function parseTelegramUserFromInitData(initData) {
    if (!BOT_TOKEN) {
        throw new Error('Не задан TELEGRAM_BOT_TOKEN');
    }

    if (!initData || typeof initData !== 'string') {
        throw new Error('Отсутствуют данные Telegram');
    }

    const params = new URLSearchParams(initData);
    const hash = params.get('hash');

    if (!hash) {
        throw new Error('Отсутствует Telegram hash');
    }

    const dataCheckString = [...params.entries()]
        .filter(([key]) => key !== 'hash')
        .sort(([keyA], [keyB]) => keyA.localeCompare(keyB))
        .map(([key, value]) => `${key}=${value}`)
        .join('\n');

    const secretKey = crypto
        .createHmac('sha256', 'WebAppData')
        .update(BOT_TOKEN)
        .digest();

    const expectedHash = crypto
        .createHmac('sha256', secretKey)
        .update(dataCheckString)
        .digest('hex');

    if (!/^[a-f0-9]{64}$/i.test(hash)) {
        throw new Error('Некорректный формат Telegram hash');
    }

    const hashBuffer = Buffer.from(hash, 'hex');
    const expectedBuffer = Buffer.from(expectedHash, 'hex');

    if (hashBuffer.length !== expectedBuffer.length) {
        throw new Error('Некорректная длина Telegram hash');
    }

    const isValid = crypto.timingSafeEqual(hashBuffer, expectedBuffer);
    if (!isValid) {
        throw new Error('Невалидные данные Telegram');
    }

    const authDate = Number(params.get('auth_date'));
    if (!Number.isFinite(authDate)) {
        throw new Error('Некорректная дата авторизации Telegram');
    }

    const nowTs = Math.floor(Date.now() / 1000);
    if (nowTs - authDate > 24 * 60 * 60) {
        throw new Error('Устаревшая Telegram-сессия');
    }

    const userRaw = params.get('user');
    if (!userRaw) {
        throw new Error('Отсутствуют данные пользователя Telegram');
    }

    let user;
    try {
        user = JSON.parse(userRaw);
    } catch {
        throw new Error('Некорректный формат Telegram user');
    }

    if (!user.id) {
        throw new Error('Отсутствует Telegram user id');
    }

    return String(user.id);
}

function ensureAdminAccess(initData) {
    const telegramId = parseTelegramUserFromInitData(initData);

    if (ADMIN_TELEGRAM_IDS.size === 0) {
        const error = new Error('Не настроен список ADMIN_TELEGRAM_IDS');
        error.status = 500;
        throw error;
    }

    if (!ADMIN_TELEGRAM_IDS.has(telegramId)) {
        const error = new Error('Доступ запрещен');
        error.status = 403;
        throw error;
    }

    return telegramId;
}

function validateRegisterPayload(payload) {
    const name = String(payload.name || '').trim();
    const phoneDigits = String(payload.phone || '').replace(/\D/g, '');
    const university = String(payload.university || '').trim();
    const consentAccepted = payload.consentAccepted === true;

    const nameRegex = /^(?=.{2,50}$)[A-Za-zА-Яа-яЁё\s-]+$/;
    if (!nameRegex.test(name)) {
        throw new Error('Некорректное имя');
    }

    if (!/^7\d{10}$/.test(phoneDigits)) {
        throw new Error('Некорректный номер телефона');
    }

    if (!ALLOWED_UNIVERSITIES.has(university)) {
        throw new Error('Некорректный университет');
    }

    if (!consentAccepted) {
        throw new Error('Необходимо согласие на обработку персональных данных');
    }

    return { name, phone: phoneDigits, university };
}

function getGoogleErrorMessage(error) {
    return (
        error?.response?.data?.error?.message ||
        error?.errors?.[0]?.message ||
        error?.message ||
        'Unknown Google API error'
    );
}

async function getStudentsRows() {
    const response = await sheets.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: `${SHEET_NAME}!A:F`,
    });

    return response.data.values || [];
}

function buildProfileFromRow(row) {
    return {
        telegram_id: row[0] || '',
        name: row[1] || '',
        phone: row[2] || '',
        university: row[3] || '',
        date: row[4] || '',
        consent_at: row[5] || '',
    };
}

async function getProfileByTelegramId(telegramId) {
    const rows = await getStudentsRows();
    const dataRows = rows.slice(1);
    const row = dataRows.find((item) => String(item[0]) === String(telegramId));

    if (!row) {
        return null;
    }

    return buildProfileFromRow(row);
}

app.post('/api/check-user', async (req, res) => {
    let telegramId;
    try {
        telegramId = parseTelegramUserFromInitData(req.body?.initData);
    } catch (error) {
        return res.status(401).json({ registered: false, message: error.message });
    }

    try {
        const profile = await getProfileByTelegramId(telegramId);
        res.json({ registered: Boolean(profile) });
    } catch (error) {
        const details = getGoogleErrorMessage(error);
        console.error('check-user error:', details, error);
        res.status(500).json({ registered: false, message: `Ошибка проверки регистрации: ${details}` });
    }
});

app.post('/api/profile', async (req, res) => {
    let telegramId;
    try {
        telegramId = parseTelegramUserFromInitData(req.body?.initData);
    } catch (error) {
        return res.status(401).json({ success: false, message: error.message });
    }

    try {
        const profile = await getProfileByTelegramId(telegramId);
        if (!profile) {
            return res.status(404).json({ success: false, message: 'Профиль не найден' });
        }

        res.json({ success: true, profile });
    } catch (error) {
        const details = getGoogleErrorMessage(error);
        console.error('profile error:', details, error);
        res.status(500).json({ success: false, message: `Ошибка загрузки профиля: ${details}` });
    }
});

app.post('/api/admin/users', async (req, res) => {
    try {
        ensureAdminAccess(req.body?.initData);
    } catch (error) {
        const status = error.status || 401;
        return res.status(status).json({ success: false, message: error.message });
    }

    const query = String(req.body?.query || '').trim().toLowerCase();
    const universityFilter = String(req.body?.university || '').trim();

    try {
        const rows = await getStudentsRows();
        const users = rows
            .slice(1)
            .map(buildProfileFromRow)
            .filter((user) => {
                if (universityFilter && user.university !== universityFilter) {
                    return false;
                }

                if (!query) {
                    return true;
                }

                const haystack = [
                    user.telegram_id,
                    user.name,
                    user.phone,
                    user.university,
                    user.date
                ].join(' ').toLowerCase();

                return haystack.includes(query);
            })
            .sort((a, b) => {
                const aTs = Date.parse(a.date) || 0;
                const bTs = Date.parse(b.date) || 0;
                return bTs - aTs;
            });

        res.json({ success: true, total: users.length, users });
    } catch (error) {
        const details = getGoogleErrorMessage(error);
        console.error('admin users error:', details, error);
        res.status(500).json({ success: false, message: `Ошибка загрузки пользователей: ${details}` });
    }
});

app.post('/api/register', async (req, res) => {
    let telegramId;
    try {
        telegramId = parseTelegramUserFromInitData(req.body?.initData);
    } catch (error) {
        return res.status(401).json({ success: false, message: error.message });
    }

    let validatedData;
    try {
        validatedData = validateRegisterPayload(req.body || {});
    } catch (error) {
        return res.status(400).json({ success: false, message: error.message });
    }

    if (activeRequests.has(telegramId)) {
        return res.status(409).json({ success: false, message: 'Запрос уже обрабатывается' });
    }

    activeRequests.add(telegramId);

    try {
        const existingProfile = await getProfileByTelegramId(telegramId);
        if (existingProfile) {
            return res.status(409).json({ success: false, message: 'Вы уже зарегистрированы' });
        }

        const nowIso = new Date().toISOString();
        await sheets.spreadsheets.values.append({
            spreadsheetId: SPREADSHEET_ID,
            range: `${SHEET_NAME}!A:F`,
            valueInputOption: 'RAW',
            requestBody: {
                values: [[
                    telegramId,
                    validatedData.name,
                    validatedData.phone,
                    validatedData.university,
                    nowIso,
                    nowIso
                ]]
            }
        });

        res.json({ success: true });
    } catch (error) {
        const details = getGoogleErrorMessage(error);
        console.error('register error:', details, error);
        res.status(500).json({ success: false, message: `Ошибка регистрации: ${details}` });
    } finally {
        activeRequests.delete(telegramId);
    }
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`Сервер запущен на порту ${PORT}`);
});
