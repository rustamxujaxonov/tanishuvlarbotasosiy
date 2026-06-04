from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup
from config import REGIONS, PREMIUM_PRICES, CHANNEL_LINK

def gender_keyboard():
    kb = ReplyKeyboardBuilder()
    kb.button(text="👨 Erkak")
    kb.button(text="👩 Ayol")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True, one_time_keyboard=True)

def region_keyboard():
    kb = ReplyKeyboardBuilder()
    for r in REGIONS:
        kb.button(text=r)
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True, one_time_keyboard=True)

def main_menu(is_premium: bool = False):
    kb = ReplyKeyboardBuilder()
    kb.button(text="🔍 Muloqotchi qidirish")
    if is_premium:
        kb.button(text="👧 Qizlar")
        kb.button(text="👦 Yigitlar")
    kb.button(text="⭐ Premium")
    kb.button(text="👤 Profilim")
    kb.adjust(1, 2 if is_premium else 1, 1, 1)
    return kb.as_markup(resize_keyboard=True)

def chat_keyboard():
    kb = ReplyKeyboardBuilder()
    kb.button(text="⏭ Keyingisi")
    kb.button(text="🚪 Chiqish")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)

def subscribe_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="📢 Kanalga a'zo bo'lish", url=CHANNEL_LINK)
    kb.button(text="✅ A'zo bo'ldim", callback_data="check_subscription")
    kb.adjust(1)
    return kb.as_markup()
