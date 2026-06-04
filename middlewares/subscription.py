from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from database.db import get_user
from keyboards.buttons import subscribe_keyboard
from config import CHANNEL_ID


class SubscriptionMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        bot = data.get("bot")
        if not bot:
            return await handler(event, data)

        if isinstance(event, Message):
            user_id = event.from_user.id
            if event.text and event.text.startswith(("/start", "/admin")):
                return await handler(event, data)
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            if event.data == "check_subscription":
                return await handler(event, data)
        else:
            return await handler(event, data)

        # Ro'yxatdan o'tmaganlarga to'sqinlik qilmaymiz
        user = await get_user(user_id)
        if not user or not user.is_registered:
            return await handler(event, data)

        # Obunani tekshiramiz
        is_subscribed = await self._check_subscription(bot, user_id)
        if not is_subscribed:
            text = "⚠️ <b>Botdan foydalanish uchun kanalga a'zo bo'lishingiz shart!</b>"
            if isinstance(event, Message):
                await event.answer(text, reply_markup=subscribe_keyboard(), parse_mode="HTML")
            else:
                await event.message.answer(text, reply_markup=subscribe_keyboard(), parse_mode="HTML")
                await event.answer()
            return

        return await handler(event, data)

    @staticmethod
    async def _check_subscription(bot, user_id: int) -> bool:
        try:
            member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
            return member.status not in ("left", "kicked", "restricted")
        except:
            return True
