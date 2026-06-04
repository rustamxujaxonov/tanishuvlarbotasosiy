import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID", 0))
CHANNEL_ID = os.getenv("CHANNEL_ID")
CHANNEL_LINK = os.getenv("CHANNEL_LINK")

PREMIUM_PRICES = {
    "1_day":  {"price": 5000,  "days": 1,  "label": "1 kun — 5,000 so'm"},
    "3_days": {"price": 12000, "days": 3,  "label": "3 kun — 12,000 so'm"},
    "1_week": {"price": 20000, "days": 7,  "label": "1 hafta — 20,000 so'm"},
    "1_month":{"price": 45000, "days": 30, "label": "1 oy — 45,000 so'm"},
}

REGIONS = [
    "Toshkent shahri", "Toshkent viloyati", "Samarqand", "Buxoro", "Andijon",
    "Farg'ona", "Namangan", "Qashqadaryo", "Surxondaryo", "Jizzax",
    "Sirdaryo", "Navoiy", "Xorazm", "Qoraqalpog'iston"
]
