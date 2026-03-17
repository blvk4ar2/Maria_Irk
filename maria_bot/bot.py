import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
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

BTN_ASSORTMENT = "Ассортимент"
BTN_BRANCH = "Найти филиал"
BTN_BONUS = "Бонусы и акции"
BTN_CHAT = "Задать вопрос"
BTN_SITE = "Сайт"
BTN_HELP = "Помощь"

BONUS_TEXT = (
    "Сейчас у нас действует персональное предлоджение для студентов БГУ и ИГУ.\n"
    "Присоедениться к программе можно по кнопке ниже:"
)

START_TEXT = (
    "🎉 Добро пожаловать в чат-бота «Мария»!\n\n"
    "Вот что вы можете здесь делать:\n\n"
    "/start — перезапустить бота\n"
    "/menu — показать главное меню\n"
    "/assortment — посмотреть наши десерты, цены и новинки\n"
    "/mariya — найти ближайший филиал\n"
    "/bonus — узнать, есть ли персональные акции и бонусы\n"
    "/chat — задать вопрос прямо здесь\n\n"
    "/site — перейти на сайт\n"
    "/help — показать этот список ещё раз\n\n"
    "Если что-то непонятно — просто напишите +...-...-..-.. . Мы рядом 😊"
)

HELP_TEXT = (
    "Список команд:\n\n"
    "/start — перезапустить бота\n"
    "/menu — показать главное меню\n"
    "/assortment — посмотреть ассортимент\n"
    "/bonus — акции и предложения\n"
    "/mariya — найти ближайший филиал\n"
    "/chat — задать вопрос\n"
    "/site — перейти на сайт\n"
    "/help — список всех команд"
)

BRANCH_TEXT = (
    "🍰 Кондитерская «Мария»\n\n"
    "Мы рады приветствовать вас в наших филиалах! Выберите ваш город, чтобы найти "
    "ближайшую кондитерскую с нашими вкусными тортами и десертами.\n\n"
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
    "🍰 Приходите к нам за свежими тортами и десертами!\n"
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


def build_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_ASSORTMENT), KeyboardButton(text=BTN_BRANCH)],
            [KeyboardButton(text=BTN_BONUS), KeyboardButton(text=BTN_CHAT)],
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


@dp.message(CommandStart())
async def on_start(message: Message) -> None:
    await message.answer(START_TEXT, reply_markup=build_main_keyboard())


@dp.message(Command("menu"))
async def on_menu(message: Message) -> None:
    await message.answer("Главное меню:", reply_markup=build_main_keyboard())


@dp.message(Command("assortment"))
async def on_assortment(message: Message) -> None:
    await message.answer("Ассортимент скоро будет здесь. Мы готовим описание и цены.")


@dp.message(Command("bonus"))
async def on_bonus(message: Message) -> None:
    keyboard = build_mini_app_keyboard()
    if keyboard is None:
        await message.answer("Ссылка на регистрацию сейчас недоступна.")
        return
    await message.answer(BONUS_TEXT, reply_markup=keyboard)


@dp.message(Command("mariya"))
async def on_mariya(message: Message) -> None:
    await message.answer(BRANCH_TEXT, reply_markup=build_city_keyboard())


@dp.message(Command("chat"))
async def on_chat(message: Message) -> None:
    await message.answer("Задайте вопрос, и мы ответим в этом чате.")


@dp.message(Command("site"))
async def on_site(message: Message) -> None:
    await message.answer(
        "🍰 Кондитерская «Мария» приветствует вас!\n\n"
        "У нас вы найдете огромный выбор свежих тортов, десертов и выпечки. "
        "Каждый день мы готовим для вас только самое вкусное и качественное!\n\n"
        "Ознакомиться со всем ассортиментом можно на нашем сайте:",
        reply_markup=build_site_keyboard(),
    )


@dp.message(Command("help"))
async def on_help(message: Message) -> None:
    await message.answer(HELP_TEXT)


@dp.message(F.text == BTN_ASSORTMENT)
async def on_assortment_button(message: Message) -> None:
    await on_assortment(message)


@dp.message(F.text == BTN_BRANCH)
async def on_branch_button(message: Message) -> None:
    await on_mariya(message)


@dp.callback_query(F.data == "city_irkutsk")
async def on_city_irkutsk(callback: CallbackQuery) -> None:
    await callback.message.answer(IRKUTSK_TEXT, reply_markup=build_back_to_city_keyboard())
    await callback.answer()


@dp.callback_query(F.data == "city_angarsk")
async def on_city_angarsk(callback: CallbackQuery) -> None:
    await callback.message.answer(ANGARSK_TEXT, reply_markup=build_back_to_city_keyboard())
    await callback.answer()


@dp.callback_query(F.data == "city_menu")
async def on_city_menu(callback: CallbackQuery) -> None:
    await callback.message.answer(BRANCH_TEXT, reply_markup=build_city_keyboard())
    await callback.answer()


@dp.message(F.text == BTN_BONUS)
async def on_bonus_button(message: Message) -> None:
    await on_bonus(message)


@dp.message(F.text == BTN_CHAT)
async def on_chat_button(message: Message) -> None:
    await on_chat(message)


@dp.message(F.text == BTN_SITE)
async def on_site_button(message: Message) -> None:
    await on_site(message)


@dp.message(F.text == BTN_HELP)
async def on_help_button(message: Message) -> None:
    await on_help(message)


async def set_bot_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Перезапуск бота"),
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
