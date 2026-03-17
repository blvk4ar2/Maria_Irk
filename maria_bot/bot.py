import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, KeyboardButton, Message, ReplyKeyboardMarkup
from dotenv import load_dotenv


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
SITE_URL = os.getenv("SITE_URL", "").strip() or "https://www.maria-irk.ru/"

BTN_ASSORTMENT = "Ассортимент"
BTN_BRANCH = "Найти филиал"
BTN_BONUS = "Бонусы и акции"
BTN_CHAT = "Задать вопрос"
BTN_SITE = "Сайт"
BTN_HELP = "Помощь"

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
    await message.answer("Акции и предложения скоро появятся. Следите за обновлениями.")


@dp.message(Command("mariya"))
async def on_mariya(message: Message) -> None:
    await message.answer("Напишите ваш район или адрес, и мы подскажем ближайший филиал.")


@dp.message(Command("chat"))
async def on_chat(message: Message) -> None:
    await message.answer("Задайте вопрос, и мы ответим в этом чате.")


@dp.message(Command("site"))
async def on_site(message: Message) -> None:
    if SITE_URL:
        await message.answer(f"Сайт: {SITE_URL}")
    else:
        await message.answer("Ссылка на сайт пока не указана.")


@dp.message(Command("help"))
async def on_help(message: Message) -> None:
    await message.answer(HELP_TEXT)


@dp.message(F.text == BTN_ASSORTMENT)
async def on_assortment_button(message: Message) -> None:
    await on_assortment(message)


@dp.message(F.text == BTN_BRANCH)
async def on_branch_button(message: Message) -> None:
    await on_mariya(message)


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
