"""
Anonim Tanishuvlar Boti
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

# Handlers
from handlers import admin, onboarding, premium, search

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN topilmadi!")
        sys.exit(1)

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Middleware ni vaqtinchalik o'chirib turamiz
    # dp.message.middleware(SubscriptionMiddleware())
    # dp.callback_query.middleware(SubscriptionMiddleware())

    # ================== ROUTER TARTIBI ==================
    dp.include_router(admin.router)
    dp.include_router(onboarding.router)
    dp.include_router(premium.router)
    dp.include_router(search.router)

    logger.info("Ma'lumotlar bazasi tayyorlanmoqda...")
    await init_db()
    logger.info("DB tayyor.")

    logger.info("Bot ishga tushmoqda...")
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        logger.info("Polling boshlandi...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
