"""
Anonim Tanishuvlar Boti
=======================
Asosiy entry point. Bot ishga tushiriladi va barcha
handler/middleware larni ro'yxatdan o'tkazadi.
"""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database.db import init_db
from middlewares.subscription import SubscriptionMiddleware

# ─── Handlerlar ───────────────────────────────────────────────
from handlers import onboarding, search, premium, admin


# ─── Logging sozlash ──────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN muhit o'zgaruvchisi topilmadi!")
        sys.exit(1)

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Middleware
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())

    # Routerlar
    dp.include_router(admin.router)
    dp.include_router(onboarding.router)
    dp.include_router(premium.router)
    dp.include_router(search.router)

    # DB
    logger.info("Ma'lumotlar bazasi tayyorlanmoqda...")
    await init_db()
    logger.info("DB tayyor.")

    # Webhook ni tozalash (ikkita marta)
    logger.info("Bot ishga tushmoqda...")
    await bot.delete_webhook(drop_pending_updates=True)
    await asyncio.sleep(1)  # qo'shimcha kutish
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        logger.info("Polling boshlandi...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
