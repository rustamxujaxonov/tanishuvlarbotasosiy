from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import PREMIUM_PRICES, ADMIN_GROUP_ID
from database.db import (
    get_user, is_premium_active,
    create_premium_request, update_premium_request
)
from keyboards.buttons import (
    main_menu, premium_plans_keyboard,
    payment_confirm_keyboard, admin_approve_keyboard
)

router = Router()


# ─── FSM holatlari ────────────────────────────────────────────
class PremiumStates(StatesGroup):
    waiting_for_receipt = State()  # Chek rasmi kutilmoqda


# ═══════════════════════════════════════════════════════════════
#  PREMIUM MENYU
# ═══════════════════════════════════════════════════════════════

@router.message(F.text == "⭐ Premium")
async def show_premium_menu(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        return

    is_prem = await is_premium_active(user.id)
    if is_prem:
        await message.answer(
            f"⭐ Siz allaqachon <b>Premium</b> foydalanuvchisiz!\n"
            f"⏳ Muddati tugaydi: <b>{user.premium_until.strftime('%d.%m.%Y %H:%M')}</b>\n\n"
            "Muddatni uzaytirish uchun quyidagi rejalardan birini tanlang:",
            reply_markup=premium_plans_keyboard(),
            parse_mode="HTML",
        )
    else:
        await message.answer(
            "⭐ <b>Premium afzalliklari:</b>\n\n"
            "✅ 👧 Qiz bola qidirish\n"
            "✅ 👦 O'g'il bola qidirish\n"
            "✅ 👤 Suhbatdosh profilini ko'rish\n"
            "✅ Tezroq juftlash\n\n"
            "📋 <b>Narxlar:</b>",
            reply_markup=premium_plans_keyboard(),
            parse_mode="HTML",
        )


# ─── Reja tanlash ─────────────────────────────────────────────
@router.callback_query(F.data.startswith("buy_premium:"))
async def select_plan(callback: CallbackQuery, state: FSMContext):
    plan_key = callback.data.split(":")[1]
    plan = PREMIUM_PRICES.get(plan_key)
    if not plan:
        await callback.answer("Noma'lum reja!", show_alert=True)
        return

    await state.update_data(selected_plan=plan_key)

    # To'lov ko'rsatmasi
    payment_details = (
        f"💳 <b>To'lov ma'lumotlari</b>\n\n"
        f"📦 Reja: <b>{plan['label']}</b>\n"
        f"💵 Narxi: <b>{plan['price']:,} so'm</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🏦 <b>To'lov usuli:</b>\n"
        f"Karta raqami: <code>8600 1234 5678 9012</code>\n"
        f"Egasi: <b>Abdullayev A.</b>\n\n"
        f"⚠️ <b>Muhim:</b> To'lov amalga oshirgandan so'ng chek rasmini yuboring!\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"«📸 Chek rasmini yuborish» tugmasini bosib, chek rasmini yuboring:"
    )

    await callback.message.edit_text(
        payment_details,
        reply_markup=payment_confirm_keyboard(plan_key),
        parse_mode="HTML",
    )
    await callback.answer()


# ─── Orqaga ───────────────────────────────────────────────────
@router.callback_query(F.data == "back_to_plans")
async def back_to_plans(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "📋 <b>Premium rejalari:</b>",
        reply_markup=premium_plans_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


# ─── Chek yuborish ────────────────────────────────────────────
@router.callback_query(F.data.startswith("send_receipt:"))
async def request_receipt(callback: CallbackQuery, state: FSMContext):
    plan_key = callback.data.split(":")[1]
    await state.update_data(selected_plan=plan_key)
    await state.set_state(PremiumStates.waiting_for_receipt)

    await callback.message.answer(
        "📸 Chek rasmini yuboring (screenshot yoki foto).\n"
        "❌ Bekor qilish uchun /cancel buyrug'ini bering."
    )
    await callback.answer()


# ─── Chek rasmini qabul qilish ───────────────────────────────
@router.message(PremiumStates.waiting_for_receipt, F.photo)
async def receive_receipt(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    plan_key = data.get("selected_plan")

    if not plan_key or plan_key not in PREMIUM_PRICES:
        await message.answer("❌ Xatolik yuz berdi. Qaytadan boshlang.")
        await state.clear()
        return

    plan = PREMIUM_PRICES[plan_key]
    photo_file_id = message.photo[-1].file_id
    user = await get_user(user_id)

    # DB ga so'rov saqlaymiz
    req = await create_premium_request(
        user_id=user_id,
        plan_key=plan_key,
        photo_file_id=photo_file_id,
    )

    # ─── Adminlar guruhiga forward ─────────────────────────
    if ADMIN_GROUP_ID:
        caption = (
            f"💰 <b>Yangi premium so'rov #{req.id}</b>\n\n"
            f"👤 Foydalanuvchi: <a href='tg://user?id={user_id}'>{user.custom_name}</a>\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"📦 Reja: <b>{plan['label']}</b>\n"
            f"💵 Narxi: <b>{plan['price']:,} so'm</b>"
        )
        admin_msg = await message.bot.send_photo(
            chat_id=ADMIN_GROUP_ID,
            photo=photo_file_id,
            caption=caption,
            reply_markup=admin_approve_keyboard(req.id, user_id),
            parse_mode="HTML",
        )
        # Admin xabar ID ni saqlaymiz
        await update_premium_request(req.id, admin_message_id=admin_msg.message_id)

    await state.clear()

    is_prem = await is_premium_active(user_id)
    await message.answer(
        "✅ <b>Chekingiz qabul qilindi!</b>\n\n"
        "⏳ Admin tekshirgandan so'ng Premium faollashtiriladi.\n"
        "Odatda 5-30 daqiqa ichida javob beriladi.",
        reply_markup=main_menu(is_premium=is_prem),
        parse_mode="HTML",
    )


@router.message(PremiumStates.waiting_for_receipt)
async def wrong_receipt_format(message: Message):
    """Rasm o'rniga boshqa narsa yuborganda"""
    if message.text == "/cancel":
        await message.answer("❌ Bekor qilindi.")
        return
    await message.answer("❌ Iltimos, <b>rasm (foto)</b> yuboring.", parse_mode="HTML")
