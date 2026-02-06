import logging

from aiogram import F, Router, types
from asgiref.sync import sync_to_async

from bot_mentor.models import TelegramUser
from bot_mentor.services.embedding_service import (
    generate_answer,
    search_relevant_chunks,
)

"""
«повседневная» логика.
RAG-поиск, ответы на вопросы про меню и прочее.
То, что доступно уже одобренным пользователям.
"""

router = Router()


async def send_smart_answer(message: types.Message, text: str):
    """
    Разрезает длинный ответ от LLM на части по 4000 символов,
    чтобы Telegram не выдавал ошибку 'message is too long'.
    parse_mode="Markdown"-что бы видел MD, меняю на html-тг ругается
    """
    MAX_LENGTH = 4000
    if len(text) <= MAX_LENGTH:
        await message.answer(
            text, parse_mode="HTML"
        )  # Если текст короткий, отправляем как обычно
    else:
        # Если текст длинный, режем его на куски
        for i in range(0, len(text), MAX_LENGTH):
            chunk = text[i : i + MAX_LENGTH]
            await message.answer(chunk, parse_mode="HTML")


@router.message(F.text)
async def handle_rag_question(message: types.Message):
    # 1. ⚡️ Проверка доступа (Middleware на минималках)
    user = await sync_to_async(
        TelegramUser.objects.filter(telegram_id=message.from_user.id).first
    )()

    if not user or not user.is_approved:
        await message.answer(
            "У тебя пока нет доступа к базе знаний. Обратись к менеджеру. 🛑"
        )
        return

    # 2. Магия RAG
    # Отправляем статус "печатает...", чтобы юзер не нервничал
    await message.bot.send_chat_action(message.chat.id, action="typing")

    try:
        # Ищем куски текста, похожие на вопрос
        # Мы вызываем синхронные функции через sync_to_async
        # chunks = await sync_to_async(search_relevant_chunks)(query=message.text)

        # 👽это временно, пока тестирую систему только с менд кухни
        chunks = await sync_to_async(search_relevant_chunks)(
            query=message.text,
            category="menu",  # 👈 Добавляем категорию (она должна совпадать с тем, что в админке)
        )

        if not chunks:
            await message.answer(
                "К сожалению, в меню пока нет информации по этому вопросу. 🧐"
            )
            return

        # Генерируем ответ на основе найденных кусков
        answer = await sync_to_async(generate_answer)(
            query=message.text, context=chunks
        )

        # Режем на кусочки сообщение-ответ, что бы тг не падал
        await send_smart_answer(message, answer)

    except Exception as e:
        logging.error(f"Ошибка RAG: {e}")
        await message.answer("Произошла ошибка при поиске ответа. Попробуй позже.")
