import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)
from dotenv import load_dotenv


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip().rstrip("/")
ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = {
    int(item.strip())
    for item in ADMIN_IDS_RAW.split(",")
    if item.strip().isdigit()
}

BTN_OPEN_APP = "Открыть приложение"
BTN_ADMIN = "Админка"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set in .env")

if not WEBAPP_URL:
    raise RuntimeError("WEBAPP_URL is not set in .env")


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def build_inline_app_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть приложение", web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
    )


def build_inline_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть админку", web_app=WebAppInfo(url=f"{WEBAPP_URL}/admin"))]
        ]
    )


dp = Dispatcher()


@dp.message(CommandStart())
async def on_start(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else 0
    await message.answer(
        "Скидки для студентов:",
        reply_markup=build_inline_app_keyboard(),
    )

    if is_admin(user_id):
        await message.answer(
            "Админ-панель:",
            reply_markup=build_inline_admin_keyboard(),
        )


@dp.message(Command("app"))
async def on_app_command(message: Message) -> None:
    await message.answer(
        "Открыть приложение:",
        reply_markup=build_inline_app_keyboard(),
    )


@dp.message(Command("admin"))
async def on_admin_command(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else 0
    if not is_admin(user_id):
        await message.answer("Доступ к админке запрещен.")
        return

    await message.answer(
        "Открыть админку:",
        reply_markup=build_inline_admin_keyboard(),
    )


@dp.message(F.text == BTN_OPEN_APP)
async def on_open_app_button(message: Message) -> None:
    await message.answer(
        "Запуск Mini App:",
        reply_markup=build_inline_app_keyboard(),
    )


@dp.message(F.text == BTN_ADMIN)
async def on_open_admin_button(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else 0
    if not is_admin(user_id):
        await message.answer("Доступ к админке запрещен.")
        return

    await message.answer(
        "Запуск админки:",
        reply_markup=build_inline_admin_keyboard(),
    )


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=BOT_TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
