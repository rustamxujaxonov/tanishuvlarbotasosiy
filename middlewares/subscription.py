from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from config import CHANNEL_ID
from database.db import get_user
from keyboards.buttons import subscribe_keyboard


class SubscriptionMiddleware(BaseMiddleware):
    """Majburiy obuna middleware"""

    EXEMPT_COMMANDS = {"/start", "/admin"}
    EXEMPT_CALLBACKS = {"check_subscription"}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        bot = data.get("bot")
        if not bot:
            return await handler(event, data)

        # Foydalanuvchi ID sini olish
        if isinstance(event, Message):
            user_id = event.from_user.id
            text = event.text or ""
            if text.startswith(tuple(self.EXEMPT_COMMANDS)):
                return await handler(event, data)
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            if event.data and event.data.startswith(tuple(self.EXEMPT_CALLBACKS)):
                return await handler(event, data)
        else:
            return await handler(event, data)

        # ================== MUHIM QISM ==================
        # Ro'yxatdan o'tmaganlarga middleware ta'sir qilmaydi
        user = await get_user(user_id)
        if not user or not user.is_registered:
            return await handler(event, data)
        # ================================================

        # Ro'yxatdan o'tganlarni faqat obunani tekshiramiz
        is_subscribed = await self._check_subscription(bot, user_id)

        if not is_subscribed:
            text = (
                "⚠️ <b>Botdan foydalanish uchun kanalimizga a'zo bo'lishingiz shart!</b>\n\n"
                "Quyidagi tugmani bosib kanalga a'zo bo'ling, so'ng «✅ A'zo bo'ldim» tugmasini bosing."
            )
            if isinstance(event, Message):
                await event.answer(text, reply_markup=subscribe_keyboard(), parse_mode="HTML")
            elif isinstance(event, CallbackQuery):
                try:
                    await event.message.edit_text(text, reply_markup=subscribe_keyboard(), parse_mode="HTML")
                except:
                    await event.message.answer(text, reply_markup=subscribe_keyboard(), parse_mode="HTML")
                await event.answer()
            return  # Bloklaymiz

        # Obuna bor — davom ettiramiz
        return await handler(event, data)

    @staticmethod
    async def _check_subscription(bot, user_id: int) -> bool:
        try:
            member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
            return member.status not in ("left", "kicked", "restricted")
        except Exception:
            # Kanal muammosi bo'lsa, vaqtinchalik ruxsat beramiz
            return True
