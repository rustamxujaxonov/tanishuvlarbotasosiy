from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

from config import REGIONS
from database.db import get_or_create_user, get_user, update_user
from keyboards.buttons import (
    gender_keyboard, region_keyboard, main_menu, subscribe_keyboard
)

router = Router()


# ═══════════════════════════════════════════════════════════════
#  /start — Botga kirish
# ═══════════════════════════════════════════════════════════════

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    user, created = await get_or_create_user(
        user_id=user_id,
        full_name=message.from_user.full_name,
        username=message.from_user.username,
    )

    # Ro'yxatdan o'tgan foydalanuvchi — asosiy menyuga
    if user.is_registered:
        is_prem = user.is_premium
        await message.answer(
            f"👋 Xush kelibsiz, <b>{user.custom_name}</b>!\n"
            "Quyidagi menyudan foydalaning:",
            reply_markup=main_menu(is_premium=is_prem),
            parse_mode="HTML",
        )
        return

    # Yangi foydalanuvchi — onboarding boshlash
    await update_user(user_id, onboarding_step=1)
    await message.answer(
        "👋 <b>Anonim Tanishuvlar</b> botiga xush kelibsiz!\n\n"
        "Ro'yxatdan o'tish uchun bir necha savollarga javob bering.\n\n"
        "📝 <b>1-qadam:</b> Ismingizni kiriting:",
        parse_mode="HTML",
    )


# ═══════════════════════════════════════════════════════════════
#  Obunani tekshirish (callback)
# ═══════════════════════════════════════════════════════════════

@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery):
    """Foydalanuvchi 'A'zo bo'ldim' tugmasini bosganida"""
    # Middleware allaqachon tekshirgan bo'ladi, lekin shu yerda xabar yangilaymiz
    user = await get_user(callback.from_user.id)
    await callback.message.delete()

    if user and user.is_registered:
        await callback.message.answer(
            "✅ Obuna tasdiqlandi! Botdan foydalanishingiz mumkin.",
            reply_markup=main_menu(is_premium=user.is_premium),
        )
    else:
        await callback.message.answer(
            "✅ Obuna tasdiqlandi!\n\n"
            "📝 <b>1-qadam:</b> Ismingizni kiriting:",
            parse_mode="HTML",
        )
    await callback.answer("✅ A'zolik tasdiqlandi!")


# ═══════════════════════════════════════════════════════════════
#  Onboarding qadamlari
# ═══════════════════════════════════════════════════════════════

@router.message(F.text)
async def onboarding_handler(message: Message):
    """Ro'yxatdan o'tish bosqichlari"""
    user_id = message.from_user.id
    user = await get_user(user_id)

    # RO'YXATDAN O'TGANLAR UCHUN BU HANDLER ISHLAMASIN!
    if not user or user.is_registered or user.onboarding_step <= 0:
        return

    # Qolgan kod o'zgarmaydi...

    # Onboarding jarayonida bo'lsa davom ettiramiz
    step = user.onboarding_step

    # ── Qadam 1: Ism ──────────────────────────────────────────
    if step == 1:
        name = message.text.strip()
        if len(name) < 2 or len(name) > 50:
            await message.answer("❌ Ism 2-50 ta harf orasida bo'lishi kerak. Qaytadan kiriting:")
            return
        if any(char.isdigit() for char in name):
            await message.answer("❌ Ismda raqam bo'lmasligi kerak. Qaytadan kiriting:")
            return

        await update_user(user_id, custom_name=name, onboarding_step=2)
        await message.answer(
            f"✅ Ism saqlandi: <b>{name}</b>\n\n"
            "📅 <b>2-qadam:</b> Yoshingizni kiriting (masalan: 22):",
            parse_mode="HTML",
        )

    # ── Qadam 2: Yosh ─────────────────────────────────────────
    elif step == 2:
        try:
            age = int(message.text.strip())
            if not (14 <= age <= 60):
                raise ValueError
        except ValueError:
            await message.answer("❌ Yosh 14 dan 60 gacha bo'lishi kerak. Qaytadan kiriting:")
            return

        await update_user(user_id, age=age, onboarding_step=3)
        await message.answer(
            f"✅ Yosh saqlandi: <b>{age}</b>\n\n"
            "🗺 <b>3-qadam:</b> Viloyatingizni tanlang:",
            reply_markup=region_keyboard(),
            parse_mode="HTML",
        )

    # ── Qadam 3: Viloyat ──────────────────────────────────────
    elif step == 3:
        if message.text.strip() not in REGIONS:
            await message.answer(
                "❌ Iltimos, quyidagi tugmalardan viloyatni tanlang:",
                reply_markup=region_keyboard(),
            )
            return

        await update_user(user_id, region=message.text.strip(), onboarding_step=4)
        await message.answer(
            f"✅ Viloyat: <b>{message.text}</b>\n\n"
            "👤 <b>4-qadam:</b> Jinsingizni tanlang:",
            reply_markup=gender_keyboard(),
            parse_mode="HTML",
        )

    # ── Qadam 4: Jins ─────────────────────────────────────────
    elif step == 4:
        gender_map = {"👨 Erkak": "male", "👩 Ayol": "female"}
        if message.text not in gender_map:
            await message.answer(
                "❌ Iltimos, tugmalardan birini tanlang:",
                reply_markup=gender_keyboard(),
            )
            return

        gender = gender_map[message.text]
        await update_user(
            user_id,
            gender=gender,
            onboarding_step=0,
            is_registered=True,
        )

        user = await get_user(user_id)
        gender_emoji = "👨" if gender == "male" else "👩"

        await message.answer(
            f"🎉 <b>Ro'yxatdan muvaffaqiyatli o'tdingiz!</b>\n\n"
            f"👤 Ism: <b>{user.custom_name}</b>\n"
            f"📅 Yosh: <b>{user.age}</b>\n"
            f"🗺 Viloyat: <b>{user.region}</b>\n"
            f"⚧ Jins: <b>{gender_emoji} {'Erkak' if gender == 'male' else 'Ayol'}</b>\n\n"
            "Endi botdan foydalanishingiz mumkin! 🚀",
            reply_markup=main_menu(is_premium=False),
            parse_mode="HTML",
        )
