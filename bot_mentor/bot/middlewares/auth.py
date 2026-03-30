import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message
from asgiref.sync import sync_to_async

from bot_mentor.models import TelegramUser


class AuthMiddleware(BaseMiddleware):
    """
    Middleware для проверки верификации пользователя в базе данных.
    """

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        # Работаем только с текстовыми сообщениями
        if not isinstance(event, Message):
            return await handler(event, data)

        user_id = event.from_user.id

        # Ищем пользователя в БД Django
        user = await sync_to_async(
            TelegramUser.objects.filter(telegram_id=user_id).first
        )()

        # Если юзер есть в базе и поле is_approved == True
        if user and user.is_approved:
            # Можно прокинуть объект юзера дальше в хэндлер через data
            data["user"] = user
            return await handler(event, data)  # Пропускаем к хэндлеру

        # Если доступа нет — прерываем цепочку и отвечаем пользователю
        logging.warning(f"🚫 Доступ запрещен для ID {user_id}")
        await event.answer(
            "У тебя пока нет доступа к базе знаний. Обратись к менеджеру. 🛑"
        )
        return
