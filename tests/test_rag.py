import os

import django

"""
Тестировачный файл
"""


# 1. Говорим Python, где лежат настройки нашего проекта
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# 2. Инициализируем Django (подключаем базу, модели и настройки)
django.setup()

# Теперь мы можем импортировать наши сервисы как обычно!
# noqa: E402 это комент, что бы flake8 не ругался на импорт в средине
from bot_mentor.services.embedding_service import (  # noqa: E402
    generate_answer,
    search_relevant_chunks,
)


def run_debug_test():
    """
    Функция для быстрой проверки нашего RAG-пайплайна.
    """
    print("🚀 Запуск теста RAG-пайплайна...")

    # Конфигурация теста
    query = "Сколько стоит борщ и какой у него состав?"
    # query = "В чем суть теоремы Ферма?"
    category = "menu"  # Мы уже знаем, что в базе лежит именно 'menu'

    print(f"🤔 Вопрос пользователя: {query}")
    print(f"📂 Поиск в категории: {category}")
    print("-" * 30)

    # ШАГ 1: Поиск (Retrieval)
    try:
        chunks = search_relevant_chunks(query, category)

        if not chunks:
            print("⚠️ Ничего не найдено. Проверь категорию в базе!")
            return

        print(f"✅ Найдено чанков: {len(chunks)}")
        for i, chunk in enumerate(chunks, 1):
            print(
                f"   [{i}] Отрывок: {chunk.chunk_text[:60]}... (Distance: {chunk.distance:.4f})"
            )

    except Exception as e:
        print(f"❌ Ошибка на этапе поиска: {e}")
        return

    print("-" * 30)

    # ШАГ 2: Генерация (Generation)
    try:
        print("🧠 GPT-4.1-nano думает над ответом...")
        answer = generate_answer(query, chunks)

        print("\n🤖 ОТВЕТ НЕЙРОСЕТИ:")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(answer)
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    except Exception as e:
        print(f"❌ Ошибка на этапе генерации: {e}")


if __name__ == "__main__":
    run_debug_test()
