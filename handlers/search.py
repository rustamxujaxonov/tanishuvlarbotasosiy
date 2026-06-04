from aiogram import Router, F
from aiogram.types import Message
from aiogram.exceptions import TelegramForbiddenError

from database.db import (
    get_user, update_user, find_partner, 
    connect_users, disconnect_users, is_premium_active
)
from database.models import GenderEnum
from keyboards.buttons import main_menu, chat_keyboard, cancel_search_keyboard

router = Router()


async def ensure_registered(message: Message) -> bool:
    user = await get_user(message.from_user.id)
    if not user or not user.is_registered:
        await message.answer("❗ Avval /start orqali ro'yxatdan o'ting.")
        return False
    return True


async def start_search(message: Message, gender_filter: GenderEnum = None):
    user_id = message.from_user.id
    user = await get_user(user_id)

    if user.current_partner_id:
        await message.answer("⚠️ Siz allaqachon chatdasiz. Avval chiqing.")
        return

    await update_user(user_id, is_searching=True, current_partner_id=None)

    partner = await find_partner(user_id, gender_filter)
    
    if partner:
        await connect_users(user_id, partner.id)
        is_prem = await is_premium_active(user_id)

        text = "✅ <b>Muloqotchi topildi!</b> Salom deng 👋\n\nYozishni boshlang!"
        await message.answer(text, reply_markup=chat_keyboard(), parse_mode="HTML")
        await message.bot.send_message(
            partner.id, text, reply_markup=chat_keyboard(), parse_mode="HTML"
        )
    else:
        await message.answer(
            "🔍 <b>Muloqotchi qidirilmoqda...</b>\n\nBiroz kuting...",
            reply_markup=cancel_search_keyboard(),
            parse_mode="HTML"
        )


@router.message(F.text == "🔍 Muloqotchi qidirish")
async def search_random(message: Message):
    if not await ensure_registered(message):
        return
    await start_search(message)


@router.message(F.text == "👧 Qizlar")
@router.message(F.text == "👦 Yigitlar")
async def search_gender(message: Message):
    if not await ensure_registered(message):
        return
    if not await is_premium_active(message.from_user.id):
        await message.answer(
            "⭐ Bu funksiya faqat <b>Premium</b> foydalanuvchilar uchun!",
            reply_markup=main_menu(False),
            parse_mode="HTML"
        )
        return
    await start_search(message)


@router.message(F.text == "❌ Qidiruvni bekor qilish")
async def cancel_search(message: Message):
    await update_user(message.from_user.id, is_searching=False)
    is_prem = await is_premium_active(message.from_user.id)
    await message.answer("✅ Qidiruv bekor qilindi.", reply_markup=main_menu(is_prem))
