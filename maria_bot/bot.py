import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.exceptions import SkipHandler
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from dotenv import load_dotenv


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
SITE_URL = os.getenv("SITE_URL", "").strip() or "https://www.maria-irk.ru/"
WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip().rstrip("/")
SUPPORT_CHAT_ID = -1003645778870

BTN_ASSORTMENT = "Ассортимент"
BTN_BRANCH = "Найти филиал"
BTN_BONUS = "Бонусы и акции"
BTN_CHAT = "Задать вопрос"
BTN_SITE = "Сайт"
BTN_HELP = "Помощь"
BTN_SUPPORT_CLOSE = "Завершить диалог"
BUTTON_TEXTS = {
    BTN_ASSORTMENT,
    BTN_BRANCH,
    BTN_BONUS,
    BTN_CHAT,
    BTN_SITE,
    BTN_HELP,
    BTN_SUPPORT_CLOSE,
}

BONUS_TEXT = (
    "🎁 Персональное предложение\n\n"
    "Сейчас действует специальная акция для студентов БГУ и ИГУ.\n\n"
    "Вы можете присоединиться к нашей программе лояльности и получать персональные бонусы и предложения.\n\n"
    "Нажмите кнопку ниже, чтобы подключиться 👇"
)

START_TEXT = (
    "🎉 Добро пожаловать в чат-бота «Мария»!\n\n"
    "Здесь вы можете:\n\n"
    "/start — перезапустить бота\n"
    "/assortment — посмотреть наши десерты, цены и новинки 🍰\n"
    "/mariya — найти ближайший филиал📍\n"
    "/bonus — узнать о персональных акциях и бонусах 🎁\n"
    "/chat — задать вопрос прямо здесь💬\n\n"
    "/site — перейти на наш сайт 🌐\n"
    "/help — показать список командℹ️\n\n"
    "Если что-то непонятно — просто напишите нам\n 📞 +...-...-..-..\n Мы всегда рядом и рады помочь 🤍"
)

HELP_TEXT = (
    "Список команд:\n\n"
    "/start — перезапустить бота\n"
    "/close — завершить диалог с поддержкой\n"
    "/assortment — посмотреть ассортимент🍰\n"
    "/bonus — акции и предложения🎁\n"
    "/mariya — найти ближайший филиал📍\n"
    "/chat — задать вопрос💬\n"
    "/site — перейти на сайт🌐\n"
    "/help — список всех команд"
)

BRANCH_TEXT = (
    "🍰 Кондитерская «Мария»\n\n"
    "Мы рады приветствовать вас в наших филиалах!\n"
    "Выберите ваш город, чтобы найти ближайшую кондитерскую с нашими свежими тортами и десертами.\n\n"
    "📍 Выберите город:"
)

IRKUTSK_TEXT = (
    "🏙️ Иркутск\n\n"
    "📍 Наши филиалы:\n\n"
    "1. Ул. Декабрьских Событий, 103\n\n"
    "2. Ул. Депутатская, 51\n\n"
    "3. Ул. Баррикад, 153\n\n"
    "4. Ул. Байкальская, 141\n\n"
    "5. Ул. Лермонтова, 81/5\n\n"
    "6. Ул. Ядринцева, 90\n\n"
    "7. Пр. Маршала Жукова, 11/4\n\n"
    "8. Ул. Лермонтова, 343/8\n\n"
    "9. Ул. Баумана, 207\n\n"
    "10. Юбилейный микрорайон, 56\n\n"
    "11. Б-р Рябикова, 96/1\n\n"
    "🍰 Ждём вас за свежими тортами и десертами!\n"
    "⏰ Режим работы: ежедневно с 8:00 до 21:00\n"
    "📞8 (395) 250-40-80"
)

ANGARSK_TEXT = (
    "🏙️ Ангарск\n\n"
    "📍 Наш филиал:\n\n"
    "1. 18-й мкр., 19\n\n"
    "🍰 Приходите к нам за свежими тортами и десертами!\n"
    "⏰ Режим работы: ежедневно с 10:00 до 21:00\n"
    "📞8 (395) 250-40-80"
)

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in .env")

SUPPORT_SESSIONS: set[int] = set()
USER_TO_TOPIC: dict[int, int] = {}
TOPIC_TO_USER: dict[int, int] = {}


def build_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_ASSORTMENT), KeyboardButton(text=BTN_BRANCH)],
            [KeyboardButton(text=BTN_BONUS), KeyboardButton(text=BTN_CHAT)],
            [KeyboardButton(text=BTN_SUPPORT_CLOSE)],
            [KeyboardButton(text=BTN_SITE), KeyboardButton(text=BTN_HELP)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
    )


def build_mini_app_keyboard() -> InlineKeyboardMarkup | None:
    if not WEBAPP_URL:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть регистрацию", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
    )


def build_site_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Открыть в браузере", url=SITE_URL)]]
    )


def build_city_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Иркутск", callback_data="city_irkutsk"),
                InlineKeyboardButton(text="Ангарск", callback_data="city_angarsk"),
            ]
        ]
    )


def build_back_to_city_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад к выбору города", callback_data="city_menu")]
        ]
    )


dp = Dispatcher()

BOT_MESSAGES: dict[int, list[int]] = {}


def track_message(chat_id: int, message_id: int) -> None:
    BOT_MESSAGES.setdefault(chat_id, []).append(message_id)


async def clear_tracked_messages(bot: Bot, chat_id: int) -> None:
    message_ids = BOT_MESSAGES.get(chat_id, [])
    for message_id in reversed(message_ids):
        try:
            await bot.delete_message(chat_id, message_id)
        except Exception:
            pass
    BOT_MESSAGES[chat_id] = []


def close_support_session(chat_id: int) -> None:
    SUPPORT_SESSIONS.discard(chat_id)


async def answer_and_track(message: Message, text: str, **kwargs) -> None:
    sent = await message.answer(text, **kwargs)
    track_message(message.chat.id, sent.message_id)


async def answer_and_track_callback(callback: CallbackQuery, text: str, **kwargs) -> None:
    if callback.message is None:
        return
    sent = await callback.message.answer(text, **kwargs)
    track_message(callback.message.chat.id, sent.message_id)


@dp.message(CommandStart())
async def on_start(message: Message) -> None:
    close_support_session(message.chat.id)
    await clear_tracked_messages(message.bot, message.chat.id)
    try:
        await message.delete()
    except Exception:
        pass
    await answer_and_track(message, START_TEXT, reply_markup=build_main_keyboard())


@dp.message(Command("menu"))
async def on_menu(message: Message) -> None:
    await answer_and_track(message, "Главное меню:", reply_markup=build_main_keyboard())


@dp.message(Command("assortment"))
async def on_assortment(message: Message) -> None:
    await answer_and_track(message, "Мы уже готовим подробное описание наших десертов, новинок и цены.\nСовсем скоро вы сможете выбрать любимые сладости прямо в боте 😋")


@dp.message(Command("bonus"))
async def on_bonus(message: Message) -> None:
    keyboard = build_mini_app_keyboard()
    if keyboard is None:
        await answer_and_track(message, "Ссылка на регистрацию сейчас недоступна.")
        return
    await answer_and_track(message, BONUS_TEXT, reply_markup=keyboard)


@dp.message(Command("mariya"))
async def on_mariya(message: Message) -> None:
    await answer_and_track(message, BRANCH_TEXT, reply_markup=build_city_keyboard())


@dp.message(Command("chat"))
async def on_chat(message: Message) -> None:
    SUPPORT_SESSIONS.add(message.chat.id)
    await answer_and_track(
        message,
        "💬 Вы в режиме поддержки.\n\n"
        "Опишите ваш вопрос или проблему как можно подробнее — оператор ответит вам в ближайшее время. "
        "Вы можете продолжать пользоваться ботом и командами.\n\n"
        "Чтобы выйти из режима поддержки, используйте /close.",
    )


@dp.message(Command("close"))
async def on_close(message: Message) -> None:
    if message.chat.id in SUPPORT_SESSIONS:
        close_support_session(message.chat.id)
        await answer_and_track(message, "Диалог с поддержкой завершен. Если нужно — напишите /chat.")
        try:
            user = message.from_user
            if user:
                topic_id = await ensure_support_topic(message.bot, message)
                await message.bot.send_message(
                    SUPPORT_CHAT_ID,
                    f"Пользователь завершил диалог: {user.full_name} ({user.id})",
                    message_thread_id=topic_id,
                )
        except Exception:
            pass
    else:
        await answer_and_track(message, "Диалог с поддержкой уже закрыт. Если нужно — напишите /chat.")


async def ensure_support_topic(bot: Bot, user: Message) -> int:
    user_id = user.from_user.id if user.from_user else 0
    if user_id in USER_TO_TOPIC:
        return USER_TO_TOPIC[user_id]

    title = f"{user.from_user.full_name} ({user_id})"
    topic = await bot.create_forum_topic(chat_id=SUPPORT_CHAT_ID, name=title)
    USER_TO_TOPIC[user_id] = topic.message_thread_id
    TOPIC_TO_USER[topic.message_thread_id] = user_id
    return topic.message_thread_id


@dp.message(F.chat.id != SUPPORT_CHAT_ID)
async def on_user_message(message: Message) -> None:
    if message.chat.id not in SUPPORT_SESSIONS:
        raise SkipHandler

    if message.text and message.text.startswith("/"):
        raise SkipHandler
    if message.text and message.text in BUTTON_TEXTS:
        raise SkipHandler

    try:
        topic_id = await ensure_support_topic(message.bot, message)
        header = f"Сообщение от {message.from_user.full_name} ({message.from_user.id})"
        await message.bot.send_message(
            SUPPORT_CHAT_ID,
            header,
            message_thread_id=topic_id,
        )

        if message.text:
            await message.bot.send_message(
                SUPPORT_CHAT_ID,
                message.text,
                message_thread_id=topic_id,
            )
        else:
            await message.copy_to(
                SUPPORT_CHAT_ID,
                message_thread_id=topic_id,
            )

        await answer_and_track(
            message,
            "Спасибо! Мы получили ваш запрос. В ближайшее время с вами свяжутся.\n"
            "Если нужно выйти из режима поддержки — напишите /close.",
        )
    except Exception:
        await message.answer("Не удалось передать сообщение в поддержку. Попробуйте позже.")


@dp.message(F.chat.id == SUPPORT_CHAT_ID)
async def on_support_message(message: Message) -> None:
    topic_id = message.message_thread_id
    if not topic_id or topic_id not in TOPIC_TO_USER:
        return

    user_id = TOPIC_TO_USER[topic_id]
    if message.text:
        await message.bot.send_message(user_id, message.text)
    else:
        await message.copy_to(user_id)


@dp.message(Command("site"))
async def on_site(message: Message) -> None:
    await answer_and_track(
        message,
        "🍰 Кондитерская «Мария» приветствует вас!\n\n"
        "У нас вы найдете огромный выбор свежих тортов, десертов и выпечки. "
        "Каждый день мы готовим для вас только самое вкусное и качественное😋\n\n"
        "Ознакомиться со всем ассортиментом можно на нашем сайте:",
        reply_markup=build_site_keyboard(),
    )


@dp.message(Command("help"))
async def on_help(message: Message) -> None:
    await answer_and_track(message, HELP_TEXT)


@dp.message(F.text == BTN_ASSORTMENT)
async def on_assortment_button(message: Message) -> None:
    await on_assortment(message)


@dp.message(F.text == BTN_BRANCH)
async def on_branch_button(message: Message) -> None:
    await on_mariya(message)


@dp.callback_query(F.data == "city_irkutsk")
async def on_city_irkutsk(callback: CallbackQuery) -> None:
    await answer_and_track_callback(
        callback,
        IRKUTSK_TEXT,
        reply_markup=build_back_to_city_keyboard(),
    )
    await callback.answer()


@dp.callback_query(F.data == "city_angarsk")
async def on_city_angarsk(callback: CallbackQuery) -> None:
    await answer_and_track_callback(
        callback,
        ANGARSK_TEXT,
        reply_markup=build_back_to_city_keyboard(),
    )
    await callback.answer()


@dp.callback_query(F.data == "city_menu")
async def on_city_menu(callback: CallbackQuery) -> None:
    await answer_and_track_callback(callback, BRANCH_TEXT, reply_markup=build_city_keyboard())
    await callback.answer()


@dp.message(F.text == BTN_BONUS)
async def on_bonus_button(message: Message) -> None:
    await on_bonus(message)


@dp.message(F.text == BTN_CHAT)
async def on_chat_button(message: Message) -> None:
    await on_chat(message)


@dp.message(F.text == BTN_SUPPORT_CLOSE)
async def on_support_close_button(message: Message) -> None:
    await on_close(message)


@dp.message(F.text == BTN_SITE)
async def on_site_button(message: Message) -> None:
    await on_site(message)


@dp.message(F.text == BTN_HELP)
async def on_help_button(message: Message) -> None:
    await on_help(message)


async def set_bot_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Перезапуск бота"),
        BotCommand(command="close", description="Завершить диалог с поддержкой"),
        BotCommand(command="menu", description="Показать главное меню"),
        BotCommand(command="assortment", description="Посмотреть ассортимент"),
        BotCommand(command="bonus", description="Акции и предложения"),
        BotCommand(command="mariya", description="Найти ближайший филиал"),
        BotCommand(command="chat", description="Задать вопрос"),
        BotCommand(command="site", description="Перейти на сайт"),
        BotCommand(command="help", description="Список всех команд"),
    ]
    await bot.set_my_commands(commands)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=BOT_TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    await set_bot_commands(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
