from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import PREMIUM_PRICES, ADMIN_GROUP_ID
from database.db import get_user, is_premium_active, create_premium_request
from keyboards.buttons import main_menu, premium_plans_keyboard

router = Router()


class PremiumStates(StatesGroup):
    waiting_for_receipt = State()


@router.message(F.text == "⭐ Premium")
async def show_premium(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        return

    is_prem = await is_premium_active(user.id)
    if is_prem:
        await message.answer(
            f"⭐ Sizda Premium faol!\nMuddati: {user.premium_until.strftime('%d.%m.%Y') if user.premium_until else ''}",
            reply_markup=main_menu(True)
        )
    else:
        await message.answer(
            "⭐ <b>Premium afzalliklari:</b>\n"
            "• Qizlar va Yigitlarni alohida qidirish\n"
            "• Suhbatdosh profilini ko'rish\n"
            "• Tezroq juftlashuv",
            reply_markup=premium_plans_keyboard(),
            parse_mode="HTML"
        )
