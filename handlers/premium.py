from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import PREMIUM_PRICES, ADMIN_GROUP_ID
from database.db import (
    get_user, is_premium_active, 
    create_premium_request, update_user, grant_premium
)
from keyboards.buttons import (
    main_menu, premium_plans_keyboard, 
    payment_confirm_keyboard
)

router = Router()


class PremiumStates(StatesGroup):
    waiting_for_receipt = State()


@router.message(F.text == "⭐ Premium")
async def show_premium_menu(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        return

    is_prem = await is_premium_active(user.id)
    if is_prem:
        await message.answer(
            f"⭐ Sizda Premium faol!\n\n"
            f"Muddati: {user.premium_until.strftime('%d.%m.%Y %H:%M') if user.premium_until else 'Cheksiz'}",
            reply_markup=main_menu(True),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "⭐ <b>Premium imkoniyatlari:</b>\n\n"
            "• 👧 Qizlar alohida qidirish\n"
            "• 👦 Yigitlar alohida qidirish\n"
            "• Tezroq juft topish\n"
            "• Suhbatdosh ma'lumotlarini ko'rish\n\n"
            "Narxlar:",
            reply_markup=premium_plans_keyboard(),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("buy_premium:"))
async def buy_premium(callback: CallbackQuery, state: FSMContext):
    plan_key = callback.data.split(":")[1]
    plan = PREMIUM_PRICES.get(plan_key)
    if not plan:
        await callback.answer("Noto'g'ri reja!", show_alert=True)
        return

    await state.update_data(plan_key=plan_key)
    await state.set_state(PremiumStates.waiting_for_receipt)

    text = (
        f"💳 <b>To'lov ma'lumotlari</b>\n\n"
        f"Reja: <b>{plan['label']}</b>\n"
        f"Narx: <b>{plan['price']:,} so'm</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Karta: <code>8600 0000 0000 0000</code>\n"  # o'zingizniki qo'ying
        f"Egasi: Abdullayev A.\n\n"
        f"✅ To'lov qilib, chek rasmini yuboring!"
    )

    await callback.message.edit_text(text, reply_markup=payment_confirm_keyboard(plan_key), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("send_receipt:"))
async def send_receipt(callback: CallbackQuery, state: FSMContext):
    plan_key = callback.data.split(":")[1]
    await state.update_data(plan_key=plan_key)
    await state.set_state(PremiumStates.waiting_for_receipt)
    await callback.message.answer("📸 Chek rasmini yuboring (screenshot).")
    await callback.answer()


@router.message(PremiumStates.waiting_for_receipt, F.photo)
async def receive_receipt(message: Message, state: FSMContext):
    data = await state.get_data()
    plan_key = data.get("plan_key")
    photo_id = message.photo[-1].file_id

    req = await create_premium_request(
        user_id=message.from_user.id,
        plan_key=plan_key,
        photo_file_id=photo_id
    )

    # Adminlarga yuborish
    if ADMIN_GROUP_ID:
        user = await get_user(message.from_user.id)
        plan = PREMIUM_PRICES[plan_key]
        caption = (
            f"💰 Yangi Premium so'rov #{req.id}\n\n"
            f"Foydalanuvchi: {user.custom_name}\n"
            f"ID: <code>{user.id}</code>\n"
            f"Reja: {plan['label']}"
        )
        await message.bot.send_photo(
            ADMIN_GROUP_ID, photo_id, caption=caption,
            parse_mode="HTML"
        )

    await state.clear()
    await message.answer(
        "✅ Chekingiz qabul qilindi!\n\nAdmin tasdiqlagandan so'ng Premium faollashadi.",
        reply_markup=main_menu(await is_premium_active(message.from_user.id))
    )


@router.message(PremiumStates.waiting_for_receipt)
async def wrong_receipt(message: Message):
    if message.text == "🔙 Bekor qilish":
        await message.answer("Bekor qilindi.", reply_markup=main_menu(False))
        return
    await message.answer("❌ Faqat rasm yuboring!")
