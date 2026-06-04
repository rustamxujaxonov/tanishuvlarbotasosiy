from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from config import REGIONS, PREMIUM_PRICES, CHANNEL_LINK


# ─── Onboarding: Jins tanlash ─────────────────────────────────
def gender_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="👨 Erkak")
    kb.button(text="👩 Ayol")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True, one_time_keyboard=True)


# ─── Onboarding: Viloyat tanlash ─────────────────────────────
def region_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    for region in REGIONS:
        kb.button(text=region)
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True, one_time_keyboard=True)


# ─── Asosiy menyu ─────────────────────────────────────────────
def main_menu(is_premium: bool = False) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    
    kb.button(text="🔍 Muloqotchi qidirish")
    
    if is_premium:
        kb.button(text="👧 Qiz bola qidirish")
        kb.button(text="👦 O'g'il bola qidirish")
    
    kb.button(text="⭐ Premium")
    kb.button(text="👤 Profilim")
    kb.button(text="⚙️ Sozlamalar")

    # To'g'ri adjust
    if is_premium:
        kb.adjust(1, 2, 1, 1)   # Qidiruv | Qiz/O'g'il | Premium | Profil | Sozlamalar
    else:
        kb.adjust(1, 1, 1, 1)   # 4 ta tugma, har biri alohida qatorda

    return kb.as_markup(resize_keyboard=True)


# ─── Chat ichidagi tugmalar ───────────────────────────────────
def chat_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="⏭ Keyingisi")
    kb.button(text="🚪 Chiqish")
    kb.button(text="🚫 Shikoyat")
    kb.adjust(2, 1)
    return kb.as_markup(resize_keyboard=True)


# ─── Qidiruv vaqtida ─────────────────────────────────────────
def cancel_search_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="❌ Qidiruvni bekor qilish")
    return kb.as_markup(resize_keyboard=True)


# ─── Majburiy obuna ───────────────────────────────────────────
def subscribe_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📢 Kanalga a'zo bo'lish", url=CHANNEL_LINK)
    kb.button(text="✅ A'zo bo'ldim", callback_data="check_subscription")
    kb.adjust(1)
    return kb.as_markup()


# ─── Premium rejalari ─────────────────────────────────────────
def premium_plans_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for key, data in PREMIUM_PRICES.items():
        kb.button(
            text=data["label"],
            callback_data=f"buy_premium:{key}"
        )
    kb.adjust(1)
    return kb.as_markup()


# ─── To'lovni tasdiqlash ─────────────────────────────────────
def payment_confirm_keyboard(plan_key: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📸 Chek rasmini yuborish", callback_data=f"send_receipt:{plan_key}")
    kb.button(text="🔙 Orqaga", callback_data="back_to_plans")
    kb.adjust(1)
    return kb.as_markup()


# ─── Admin: Premium tasdiqlash tugmalari ─────────────────────
def admin_approve_keyboard(request_id: int, user_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for key, data in PREMIUM_PRICES.items():
        kb.button(
            text=f"✅ {data['label']} ber",
            callback_data=f"admin_approve:{request_id}:{user_id}:{key}"
        )
    kb.button(
        text="❌ Rad etish",
        callback_data=f"admin_reject:{request_id}:{user_id}"
    )
    kb.adjust(1)
    return kb.as_markup()


# ─── Profil ko'rish (premium uchun) ──────────────────────────
def view_profile_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="👤 Suhbatdosh profilini ko'rish", callback_data="view_partner_profile")
    return kb.as_markup()
