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
    """Asosiy qidiruv funksiyasi"""
    user_id = message.from_user.id
    user = await get_user(user_id)

    # Agar allaqachon chatda bo'lsa
    if user.current_partner_id:
        await message.answer("⚠️ Siz allaqachon suhbatdasiz. Avval «🚪 Chiqish» tugmasini bosing.")
        return

    # Qidiruv holatiga o'tkazamiz
    await update_user(user_id, is_searching=True, current_partner_id=None)

    # Partner qidirish
    partner = await find_partner(user_id, gender_filter)

    if partner:
        # Juft topildi!
        await connect_users(user_id, partner.id)
        is_prem = await is_premium_active(user_id)

        text = "✅ <b>Muloqotchi topildi!</b>\n\nSalom deb yozing 👋"
        
        await message.answer(text, reply_markup=chat_keyboard(), parse_mode="HTML")
        await message.bot.send_message(
            partner.id, text, reply_markup=chat_keyboard(), parse_mode="HTML"
        )
    else:
        # Navbatga qo'yamiz
        await message.answer(
            "🔍 <b>Muloqotchi qidirilmoqda...</b>\n\n"
            "Tez orada ulanasiz. Kuting...",
            reply_markup=cancel_search_keyboard(),
            parse_mode="HTML"
        )


# ================== HANDLERS ==================

@router.message(F.text == "🔍 Muloqotchi qidirish")
async def search_random(message: Message):
    if not await ensure_registered(message):
        return
    await start_search(message, gender_filter=None)


@router.message(F.text == "👧 Qizlar")
@router.message(F.text == "👦 Yigitlar")
async def search_by_gender(message: Message):
    if not await ensure_registered(message):
        return

    if not await is_premium_active(message.from_user.id):
        await message.answer(
            "⭐ Bu funksiya faqat <b>Premium</b> foydalanuvchilar uchun!\n\n"
            "Premium sotib olish uchun «⭐ Premium» tugmasini bosing.",
            reply_markup=main_menu(False),
            parse_mode="HTML"
        )
        return

    gender_filter = GenderEnum.female if "Qizlar" in message.text else GenderEnum.male
    await start_search(message, gender_filter=gender_filter)


@router.message(F.text == "❌ Qidiruvni bekor qilish")
async def cancel_search(message: Message):
    user_id = message.from_user.id
    await update_user(user_id, is_searching=False)
    is_prem = await is_premium_active(user_id)
    await message.answer(
        "✅ Qidiruv bekor qilindi.",
        reply_markup=main_menu(is_prem)
    )


@router.message(F.text == "🚪 Chiqish")
async def leave_chat(message: Message):
    user_id = message.from_user.id
    partner_id = await disconnect_users(user_id)
    is_prem = await is_premium_active(user_id)

    await message.answer(
        "🚪 Chatdan chiqdingiz.",
        reply_markup=main_menu(is_prem)
    )

    if partner_id:
        partner_prem = await is_premium_active(partner_id)
        try:
            await message.bot.send_message(
                partner_id,
                "⚠️ Suhbatdosh chatdan chiqdi.",
                reply_markup=main_menu(partner_prem)
            )
        except TelegramForbiddenError:
            pass


@router.message(F.text == "⏭ Keyingisi")
async def next_partner(message: Message):
    user_id = message.from_user.id
    partner_id = await disconnect_users(user_id)

    if partner_id:
        try:
            partner_prem = await is_premium_active(partner_id)
            await message.bot.send_message(
                partner_id,
                "⚠️ Suhbatdosh yangi suhbatdosh qidirmoqda.",
                reply_markup=main_menu(partner_prem)
            )
        except:
            pass

    await start_search(message)  # Yangi qidiruv
