from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

from config import REGIONS
from database.db import get_or_create_user, get_user, update_user, is_premium_active
from keyboards.buttons import (
    gender_keyboard, region_keyboard, main_menu, subscribe_keyboard
)

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    user, created = await get_or_create_user(
        user_id=user_id,
        full_name=message.from_user.full_name,
        username=message.from_user.username,
    )

    if user.is_registered:
        is_prem = await is_premium_active(user_id)
        await message.answer(
            f"👋 Xush kelibsiz, <b>{user.custom_name}</b>!",
            reply_markup=main_menu(is_premium=is_prem),
            parse_mode="HTML",
        )
        return

    await update_user(user_id, onboarding_step=1)
    await message.answer(
        "👋 <b>Anonim Tanishuvlar</b> botiga xush kelibsiz!\n\n"
        "Ro'yxatdan o'tish uchun savollarga javob bering.\n\n"
        "📝 <b>1-qadam:</b> Ismingizni kiriting:",
        parse_mode="HTML",
    )


@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    await callback.message.delete()

    if user and user.is_registered:
        is_prem = await is_premium_active(user.id)
        await callback.message.answer(
            "✅ Obuna tasdiqlandi!", 
            reply_markup=main_menu(is_premium=is_prem),
            parse_mode="HTML"
        )
    else:
        await callback.message.answer(
            "✅ Obuna tasdiqlandi!\n\n📝 <b>1-qadam:</b> Ismingizni kiriting:",
            parse_mode="HTML"
        )
    await callback.answer()


@router.message(F.text)
async def onboarding_handler(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)

    if not user or user.is_registered or user.onboarding_step <= 0:
        return

    step = user.onboarding_step

    if step == 1:  # Ism
        name = message.text.strip()
        if len(name) < 2 or len(name) > 50 or any(char.isdigit() for char in name):
            await message.answer("❌ Ism 2-50 ta harf bo'lishi kerak va raqam bo'lmasin.")
            return
        await update_user(user_id, custom_name=name, onboarding_step=2)
        await message.answer(f"✅ Ism saqlandi: <b>{name}</b>\n\n📅 Yosh kiriting (14-60):", parse_mode="HTML")

    elif step == 2:  # Yosh
        try:
            age = int(message.text.strip())
            if not 14 <= age <= 60:
                raise ValueError
        except:
            await message.answer("❌ Yosh 14-60 oralig'ida bo'lishi kerak.")
            return
        await update_user(user_id, age=age, onboarding_step=3)
        await message.answer("🗺 Viloyatni tanlang:", reply_markup=region_keyboard(), parse_mode="HTML")

    elif step == 3:  # Viloyat
        if message.text not in REGIONS:
            await message.answer("Iltimos, tugmalardan tanlang:", reply_markup=region_keyboard())
            return
        await update_user(user_id, region=message.text, onboarding_step=4)
        await message.answer("👤 Jinsingizni tanlang:", reply_markup=gender_keyboard(), parse_mode="HTML")

    elif step == 4:  # Jins
        gender_map = {"👨 Erkak": "male", "👩 Ayol": "female"}
        if message.text not in gender_map:
            return
        gender = gender_map[message.text]
        await update_user(user_id, gender=gender, onboarding_step=0, is_registered=True)

        await message.answer(
            "🎉 <b>Ro'yxatdan muvaffaqiyatli o'tdingiz!</b>\n\nEndi botdan foydalanishingiz mumkin! 🚀",
            reply_markup=main_menu(is_premium=False),
            parse_mode="HTML"
        )
