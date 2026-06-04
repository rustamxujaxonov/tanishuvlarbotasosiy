import os
from dotenv import load_dotenv

load_dotenv()

# ─── Bot sozlamalari ───────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# ─── Database ─────────────────────────────────────────────────
DATABASE_URL: str = os.getenv("DATABASE_URL", "")
# Railway postgres URL ba'zan "postgres://" bilan keladi,
# SQLAlchemy uchun "postgresql+asyncpg://" kerak
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# ─── Admin sozlamalari ─────────────────────────────────────────
# Admin Telegram ID lari (vergul bilan ajratilgan)
ADMIN_IDS: list[int] = [
    int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
]
# Adminlar guruhi - cheklar shu guruhga forward qilinadi
ADMIN_GROUP_ID: int = int(os.getenv("ADMIN_GROUP_ID", "0"))

# ─── Majburiy obuna kanali ─────────────────────────────────────
# Misol: @mening_kanalim yoki -1001234567890
CHANNEL_ID: str = os.getenv("CHANNEL_ID", "@your_channel")
CHANNEL_LINK: str = os.getenv("CHANNEL_LINK", "https://t.me/your_channel")

# ─── Premium narxlari (so'm) ──────────────────────────────────
PREMIUM_PRICES = {
    "1_day":   {"price": 5_000,  "days": 1,  "label": "1 kun  — 5,000 so'm"},
    "3_days":  {"price": 10_000, "days": 3,  "label": "3 kun  — 10,000 so'm"},
    "1_week":  {"price": 15_000, "days": 7,  "label": "1 hafta — 15,000 so'm"},
    "1_month": {"price": 30_000, "days": 30, "label": "1 oy   — 30,000 so'm"},
}

# ─── Viloyatlar ro'yxati ───────────────────────────────────────
REGIONS = [
    "Toshkent shahri", "Toshkent viloyati", "Samarqand", "Buxoro",
    "Andijon", "Farg'ona", "Namangan", "Qashqadaryo", "Surxondaryo",
    "Jizzax", "Sirdaryo", "Navoiy", "Xorazm", "Qoraqalpog'iston",
]
