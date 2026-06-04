from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramForbiddenError

from database.db import (
    get_user, update_user, find_partner,
    connect_users, disconnect_users, is_premium_active
)
from database.models import GenderEnum
from keyboards.buttons import (
    main_menu, chat_keyboard, cancel_search_keyboard,
    premium_plans_keyboard, view_profile_keyboard
)

router = Router()


# ─── Yordamchi: foydalanuvchi chatda ekanligini tekshirish ────
async def ensure_registered(message: Message) -> bool:
    user = await get_user(message.from_user.id)
    if not user or not user.is_registered:
        await message.answer("❗ Avval /start orqali ro'yxatdan o'ting.")
        return False
    return True


# ═══════════════════════════════════════════════════════════════
#  QIDIRUV
# ═══════════════════════════════════════════════════════════════

async def start_search(message: Message, gender_filter: GenderEnum = None):
    """Qidiruvni boshlash (ichki funksiya)"""
    user_id = message.from_user.id
    user = await get_user(user_id)

    # Agar allaqachon chatda bo'lsa
    if user.current_partner_id:
        await message.answer("⚠️ Siz allaqachon chat ichida turibsiz. Avval /stop buyrug'ini bering.")
        return

    # Qidiruv holatiga o'tkazamiz
    await update_user(user_id, is_searching=True, current_partner_id=None)

    # Partner qidirish
    partner = await find_partner(user_id, gender_filter=gender_filter)

    if partner:
        # Partner topildi — ulaymiz
        await connect_users(user_id, partner.id)
        is_prem = await is_premium_active(user_id)
        partner_is_prem = await is_premium_active(partner.id)

        # Foydalanuvchiga xabar
        user_text = "✅ <b>Muloqotchi topildi!</b> Salom deng 👋\n\n🚪 Chatdan chiqish uchun «Chiqish» tugmasini bosing."
        partner_text = "✅ <b>Muloqotchi topildi!</b> Salom deng 👋\n\n🚪 Chatdan chiqish uchun «Chiqish» tugmasini bosing."

        user_kb = chat_keyboard()
        partner_kb = chat_keyboard()

        # Premium foydalanuvchi partner profilini ko'ra oladi
        if is_prem:
            user_text += f"\n\n👤 Suhbatdosh: <b>{partner.custom_name}</b>, {partner.age} yosh, {partner.region}"
        if partner_is_prem:
            partner_text += f"\n\n👤 Suhbatdosh: <b>{user.custom_name}</b>, {user.age} yosh, {user.region}"

        await message.answer(user_text, reply_markup=user_kb, parse_mode="HTML")
        await message.bot.send_message(
            partner.id, partner_text, reply_markup=partner_kb, parse_mode="HTML"
        )
    else:
        # Partner yo'q — kutamiz
        await message.answer(
            "🔍 <b>Muloqotchi qidirilmoqda...</b>\n\n"
            "Biroz kuting, tez orada ulanasiz!",
            reply_markup=cancel_search_keyboard(),
            parse_mode="HTML",
        )


@router.message(F.text == "🔍 Muloqotchi qidirish")
async def search_random(message: Message):
    if not await ensure_registered(message):
        return
    await start_search(message, gender_filter=None)


@router.message(F.text == "👧 Qiz bola qidirish")
async def search_female(message: Message):
    if not await ensure_registered(message):
        return
    if not await is_premium_active(message.from_user.id):
        await message.answer(
            "⭐ Bu funksiya faqat <b>Premium</b> foydalanuvchilar uchun!\n\n"
            "Premium sotib olish uchun «⭐ Premium» tugmasini bosing.",
            reply_markup=main_menu(is_premium=False),
            parse_mode="HTML",
        )
        return
    await start_search(message, gender_filter=GenderEnum.female)


@router.message(F.text == "👦 O'g'il bola qidirish")
async def search_male(message: Message):
    if not await ensure_registered(message):
        return
    if not await is_premium_active(message.from_user.id):
        await message.answer(
            "⭐ Bu funksiya faqat <b>Premium</b> foydalanuvchilar uchun!\n\n"
            "Premium sotib olish uchun «⭐ Premium» tugmasini bosing.",
            reply_markup=main_menu(is_premium=False),
            parse_mode="HTML",
        )
        return
    await start_search(message, gender_filter=GenderEnum.male)


@router.message(F.text == "❌ Qidiruvni bekor qilish")
async def cancel_search(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    if user and user.is_searching:
        await update_user(user_id, is_searching=False)
        is_prem = await is_premium_active(user_id)
        await message.answer(
            "✅ Qidiruv bekor qilindi.",
            reply_markup=main_menu(is_premium=is_prem),
        )


# ═══════════════════════════════════════════════════════════════
#  CHAT: Xabarlarni uzatish
# ═══════════════════════════════════════════════════════════════

@router.message(F.text == "🚪 Chiqish")
async def leave_chat(message: Message):
    user_id = message.from_user.id
    partner_id = await disconnect_users(user_id)
    is_prem = await is_premium_active(user_id)

    await message.answer(
        "🚪 Chatdan chiqdingiz.",
        reply_markup=main_menu(is_premium=is_prem),
    )
    if partner_id:
        partner_prem = await is_premium_active(partner_id)
        try:
            await message.bot.send_message(
                partner_id,
                "⚠️ Suhbatdosh chatdan chiqdi.\n\nYangi muloqotchi topish uchun «🔍 Muloqotchi qidirish» tugmasini bosing.",
                reply_markup=main_menu(is_premium=partner_prem),
            )
        except TelegramForbiddenError:
            pass  # Foydalanuvchi botni bloklagan


@router.message(F.text == "⏭ Keyingisi")
async def next_partner(message: Message):
    """Joriy suhbatdoshdan voz kechib, yangisini qidirish"""
    user_id = message.from_user.id
    partner_id = await disconnect_users(user_id)

    if partner_id:
        partner_prem = await is_premium_active(partner_id)
        try:
            await message.bot.send_message(
                partner_id,
                "⚠️ Suhbatdosh chatdan chiqdi.\n\nYangi muloqotchi topish uchun «🔍 Muloqotchi qidirish» tugmasini bosing.",
                reply_markup=main_menu(is_premium=partner_prem),
            )
        except TelegramForbiddenError:
            pass

    await start_search(message, gender_filter=None)


@router.message(F.text == "🚫 Shikoyat")
async def report_user(message: Message):
    """Shikoyat — hozircha oddiy xabar"""
    await message.answer(
        "🚫 Shikoyat qabul qilindi. Adminlar ko'rib chiqadi.\n\n"
        "Shikoyatdan so'ng yangi muloqotchi qidirish tavsiya etiladi."
    )


# ═══════════════════════════════════════════════════════════════
#  CHAT: Barcha turdagi xabarlarni forward qilish
# ═══════════════════════════════════════════════════════════════

CHAT_BUTTONS = {"⏭ Keyingisi", "🚪 Chiqish", "🚫 Shikoyat"}


@router.message()
async def relay_message(message: Message):
    """
    Foydalanuvchi chat ichida bo'lsa, barcha xabarlarni
    anonim tarzda suhbatdoshga yuboradi.
    """
    user_id = message.from_user.id

    # Tugmalar tekstini o'tkazib yuboramiz
    if message.text and message.text in CHAT_BUTTONS:
        return

    user = await get_user(user_id)
    if not user or not user.current_partner_id:
        return  # Chat yo'q — e'tibor bermaymiz

    partner_id = user.current_partner_id

    try:
        # Xabar turini aniqlab, tegishlicha yuboramiz
        if message.text:
            await message.bot.send_message(partner_id, message.text)
        elif message.photo:
            await message.bot.send_photo(
                partner_id, message.photo[-1].file_id,
                caption=message.caption or ""
            )
        elif message.video:
            await message.bot.send_video(
                partner_id, message.video.file_id,
                caption=message.caption or ""
            )
        elif message.voice:
            await message.bot.send_voice(partner_id, message.voice.file_id)
        elif message.video_note:
            await message.bot.send_video_note(partner_id, message.video_note.file_id)
        elif message.sticker:
            await message.bot.send_sticker(partner_id, message.sticker.file_id)
        elif message.audio:
            await message.bot.send_audio(partner_id, message.audio.file_id)
        elif message.document:
            await message.bot.send_document(
                partner_id, message.document.file_id,
                caption=message.caption or ""
            )
        elif message.animation:
            await message.bot.send_animation(partner_id, message.animation.file_id)
        elif message.location:
            await message.bot.send_location(
                partner_id,
                latitude=message.location.latitude,
                longitude=message.location.longitude,
            )
    except TelegramForbiddenError:
        # Partner botni bloklagan
        await disconnect_users(partner_id)
        is_prem = await is_premium_active(user_id)
        await message.answer(
            "⚠️ Suhbatdosh botni bloklab qo'ygan. Chat yakunlandi.",
            reply_markup=main_menu(is_premium=is_prem),
        )


# ═══════════════════════════════════════════════════════════════
#  PROFIL VA SOZLAMALAR
# ═══════════════════════════════════════════════════════════════

@router.message(F.text == "👤 Profilim")
async def show_profile(message: Message):
    user = await get_user(message.from_user.id)
    if not user or not user.is_registered:
        return

    gender_emoji = "👨" if user.gender and user.gender.value == "male" else "👩"
    premium_status = "⭐ Premium" if await is_premium_active(user.id) else "👤 Oddiy"
    premium_until = ""
    if user.premium_until:
        premium_until = f"\n⏳ Premium tugaydi: <b>{user.premium_until.strftime('%d.%m.%Y %H:%M')}</b>"

    await message.answer(
        f"👤 <b>Sizning profilingiz</b>\n\n"
        f"📝 Ism: <b>{user.custom_name}</b>\n"
        f"📅 Yosh: <b>{user.age}</b>\n"
        f"🗺 Viloyat: <b>{user.region}</b>\n"
        f"⚧ Jins: <b>{gender_emoji} {'Erkak' if user.gender and user.gender.value == 'male' else 'Ayol'}</b>\n"
        f"🏆 Status: <b>{premium_status}</b>{premium_until}",
        parse_mode="HTML",
    )
