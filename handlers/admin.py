from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from config import ADMIN_IDS, PREMIUM_PRICES
from database.db import get_user, update_user, grant_premium

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "🔐 <b>Admin Panel</b>\n\n"
        "/stats - Statistika\n"
        "/give_premium [user_id] [1_day|3_days|1_week|1_month] - Premium berish",
        parse_mode="HTML"
    )


@router.message(Command("stats"))
async def admin_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    # Oddiy statistika (to'liqroq qilish mumkin)
    await message.answer("📊 Statistika funksiyasi tez orada qo'shiladi.")


@router.message(Command("give_premium"))
async def give_premium_cmd(message: Message):
    if not is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Foydalanish: /give_premium [user_id] [1_day]")
        return

    try:
        user_id = int(parts[1])
        plan_key = parts[2]
        if plan_key not in PREMIUM_PRICES:
            await message.answer("Noto'g'ri reja!")
            return

        days = PREMIUM_PRICES[plan_key]["days"]
        until = await grant_premium(user_id, days)
        await message.answer(f"✅ {user_id} ga Premium berildi!")
    except:
        await message.answer("Xatolik yuz berdi.")
