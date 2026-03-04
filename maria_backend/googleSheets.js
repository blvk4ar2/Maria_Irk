const { google } = require('googleapis');
const path = require('path');

const scopes = ['https://www.googleapis.com/auth/spreadsheets'];

const authOptions = { scopes };
const credentialsJson =
    process.env.GOOGLE_CREDENTIALS ||
    process.env.GOOGLE_CREDENTIALS_JSON;

function normalizePrivateKey(privateKey) {
    if (typeof privateKey !== 'string') {
        return privateKey;
    }

    let normalized = privateKey.trim();
    if (
        (normalized.startsWith('"') && normalized.endsWith('"')) ||
        (normalized.startsWith("'") && normalized.endsWith("'"))
    ) {
        normalized = normalized.slice(1, -1);
    }

    normalized = normalized.replace(/\\n/g, '\n');
    normalized = normalized.replace(/\r\n/g, '\n');
    return normalized;
}

if (credentialsJson) {
    try {
        const parsed = JSON.parse(credentialsJson);
        if (parsed.private_key && typeof parsed.private_key === 'string') {
            parsed.private_key = normalizePrivateKey(parsed.private_key);
        }
        authOptions.credentials = parsed;
    } catch (error) {
        throw new Error(`Google credentials JSON is invalid: ${error.message}`);
    }
} else {
    authOptions.keyFile = process.env.GOOGLE_APPLICATION_CREDENTIALS
        ? path.resolve(process.cwd(), process.env.GOOGLE_APPLICATION_CREDENTIALS)
        : path.join(__dirname, 'credentials.json');
}

const auth = new google.auth.GoogleAuth(authOptions);

const sheets = google.sheets({ version: 'v4', auth });

module.exports = sheets;
