from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup
from config import REGIONS, PREMIUM_PRICES, CHANNEL_LINK


def gender_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="👨 Erkak")
    kb.button(text="👩 Ayol")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True, one_time_keyboard=True)


def region_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    for region in REGIONS:
        kb.button(text=region)
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True, one_time_keyboard=True)


def main_menu(is_premium: bool = False) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="🔍 Muloqotchi qidirish")
    if is_premium:
        kb.button(text="👧 Qizlar")
        kb.button(text="👦 Yigitlar")
    kb.button(text="⭐ Premium")
    kb.button(text="👤 Profilim")
    kb.button(text="⚙️ Sozlamalar")
    
    if is_premium:
        kb.adjust(1, 2, 1, 1)
    else:
        kb.adjust(1, 1, 1, 1)
    return kb.as_markup(resize_keyboard=True)


def chat_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="⏭ Keyingisi")
    kb.button(text="🚪 Chiqish")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)


def cancel_search_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="❌ Qidiruvni bekor qilish")
    return kb.as_markup(resize_keyboard=True)


def subscribe_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📢 Kanalga a'zo bo'lish", url=CHANNEL_LINK)
    kb.button(text="✅ A'zo bo'ldim", callback_data="check_subscription")
    kb.adjust(1)
    return kb.as_markup()


def premium_plans_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for key, data in PREMIUM_PRICES.items():
        kb.button(text=data["label"], callback_data=f"buy_premium:{key}")
    kb.adjust(1)
    return kb.as_markup()
