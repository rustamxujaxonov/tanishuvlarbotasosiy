from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from config import CHANNEL_ID
from keyboards.buttons import subscribe_keyboard


class SubscriptionMiddleware(BaseMiddleware):
    """
    Har bir so'rovdan oldin kanalga a'zolikni tekshiradi.
    /start komandasi va a'zolikni tekshirish callbacki bundan mustasno.
    """

    EXEMPT_COMMANDS = {"/start", "/admin"}
    EXEMPT_CALLBACKS = {"check_subscription"}
    EXEMPT_STATES = True  # yoki onboarding_step tekshirish

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Foydalanuvchi va bot obyektlarini olamiz
        bot = data.get("bot")
        user = None

        if isinstance(event, Message):
            user = event.from_user
            # Mustasno komandalar
            if event.text and any(event.text.startswith(cmd) for cmd in self.EXEMPT_COMMANDS):
                return await handler(event, data)

        elif isinstance(event, CallbackQuery):
            user = event.from_user
            # Mustasno callbacklar
            if event.data and any(event.data.startswith(cb) for cb in self.EXEMPT_CALLBACKS):
                return await handler(event, data)

        if user is None or bot is None:
            return await handler(event, data)

        # Kanalga a'zolikni tekshiramiz
        is_subscribed = await self._check_subscription(bot, user.id)

        if not is_subscribed:
            text = (
                "⚠️ <b>Botdan foydalanish uchun kanalimizga a'zo bo'lishingiz shart!</b>\n\n"
                "Quyidagi tugmani bosib kanalga a'zo bo'ling, so'ng «✅ A'zo bo'ldim» tugmasini bosing."
            )
            if isinstance(event, Message):
                await event.answer(text, reply_markup=subscribe_keyboard(), parse_mode="HTML")
            elif isinstance(event, CallbackQuery):
                await event.message.answer(text, reply_markup=subscribe_keyboard(), parse_mode="HTML")
                await event.answer()
            return  # Handlerni ishga tushirmaymiz

        return await handler(event, data)

    @staticmethod
    async def _check_subscription(bot, user_id: int) -> bool:
        try:
            from config import CHANNEL_ID
            member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
            # member.status 'left', 'kicked' yoki 'restricted' bo'lsa False qaytaradi
            return member.status not in ("left", "kicked")
        except Exception as e:
            # SHU YERGA E'TIBOR BERING:
            # Agar bu yerda xato chiqsa, bot konsolda ko'rsatishi kerak
            print(f"Kanalni tekshirishda KRITIK XATO: {e}")
            return False # Agar tekshira olmasa, foydalanuvchini bloklab turadi
