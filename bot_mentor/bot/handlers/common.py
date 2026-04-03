import logging

from aiogram import F, Router, types
from asgiref.sync import sync_to_async

from bot_mentor.models import Question
from bot_mentor.services.embedding_service import search_relevant_chunks

"""
«повседневная» логика.
поиск, ответы на вопросы про меню и прочее.
То, что доступно уже одобренным пользователям.
"""

router = Router()


async def send_smart_answer(message: types.Message, text: str):
    """
    Разрезает длинный ответ на части по 4000 символов,
    чтобы Telegram не выдавал ошибку 'message is too long'.
    parse_mode="Markdown"-что бы видел MD, меняю на html-тг ругается
    стараясь не ломать структуру HTML
    """

    MAX_LENGTH = 4000
    separator = "\n\n─────────────────────\n\n"

    if len(text) <= MAX_LENGTH:
        await message.answer(text, parse_mode="HTML")
        return

    remaining_text = text

    while len(remaining_text) > MAX_LENGTH:
        # Ищем последний separator в первом MAX_LENGTH куске
        split_pos = remaining_text.rfind(separator, 0, MAX_LENGTH)

        # Если разделитель "\n\n──────\n\n"не найден.
        if split_pos == -1:
            # Тогда ищем запасной вариант: последний перенос строки.
            split_pos = remaining_text.rfind("\n", 0, MAX_LENGTH)

        # Если даже перевод строки не найден.
        if split_pos == -1:
            # Тогда режем грубо по длине.
            split_pos = MAX_LENGTH

        # Берём кусок текста от начала до split_pos
        chunk = remaining_text[:split_pos]

        # Если кусок пустышка, режем по длине
        if not chunk.strip():
            chunk = remaining_text[:MAX_LENGTH]
            split_pos = MAX_LENGTH

        # Отправляем найденный кусок пользователю.
        await message.answer(chunk, parse_mode="HTML")

        # Отрезаем уже отправленную часть и оставляем только хвост.
        remaining_text = remaining_text[split_pos:]

        # Проверяем: а не начинается ли оставшийся текст с нашего разделителя
        if remaining_text.startswith(separator):
            # Если начинается с разделителя — убираем его целиком, чтобы следующее сообщение не стартовало с одной голой линии.
            remaining_text = remaining_text[len(separator) :]
        else:
            remaining_text = remaining_text.lstrip("\n")

    if remaining_text.strip():
        await message.answer(remaining_text, parse_mode="HTML")


@router.message(F.text)
async def handle_rag_question(message: types.Message):
    """
    Принимаем запросы пользователя, ищем релевантные чанки,
    формируем ответ и логируем вопрос в БД.
    Выводим в ТГ-бота
    """

    query = message.text.strip()
    user_id = message.from_user.id

    # Отправляем статус "печатает...", чтобы юзер не нервничал
    await message.bot.send_chat_action(message.chat.id, action="typing")

    try:
        # Вызываем наш "умный" поиск (Type 1 -> Type 2)
        chunks = await sync_to_async(search_relevant_chunks)(query=query)

        if not chunks:
            not_found_text = "К сожалению, ничего не нашлось. Попробуй другое слово! 🧐"

            await sync_to_async(Question.objects.create)(
                user_id=user_id,
                question_text=query,
                answer_text=not_found_text,
            )

            await message.answer(not_found_text)
            return

        # ПРЕОБРАЗОВАНИЕ: Список объектов -> Одна строка текста
        # Мы берем chunk_text из каждого объекта и соединяем их через разделитель

        formatted_response = "\n\n─────────────────────\n\n".join(
            [c.chunk_text for c in chunks]
        )

        # Сначала логируем
        await sync_to_async(Question.objects.create)(
            user_id=user_id,
            question_text=query,
            answer_text=formatted_response,
        )

        # Отправляем пользователю, полученные чанки режу на куски для ответа
        await send_smart_answer(message, formatted_response)

    except Exception as e:
        error_text = "🧬 Что-то пошло не так при поиске. 🛠"
        logging.error(f"❌ Ошибка в хэндлере: {e}")

        try:
            await sync_to_async(Question.objects.create)(
                user_id=user_id,
                question_text=query,
                answer_text=f"ERROR: {str(e)}",
            )
        except Exception as log_error:
            logging.error(f"❌ Не удалось записать лог Question: {log_error}")

        await message.answer(error_text)
