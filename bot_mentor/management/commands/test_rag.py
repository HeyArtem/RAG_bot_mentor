from django.core.management.base import BaseCommand

from bot_mentor.services.embedding_service import (
    generate_answer,
    search_relevant_chunks,
)

"""
Что бы не писать тесты в консоли, я использую инструмент — Management Commands (команды управления).
И уже его буду запускать из консоли
"""


class Command(BaseCommand):
    help = "Тестовый запуск RAG системы: Поиск + Генерация ответа"

    def add_arguments(self, parser):
        # Позволяет передавать вопрос прямо в консоли
        parser.add_argument("query", type=str, help="Вопрос к ИИ")
        parser.add_argument(
            "--category", type=str, default="menu", help="Категория поиска"
        )

    def handle(self, *args, **options):
        query = options["query"]
        category = options["category"]

        self.stdout.write(self.style.SUCCESS(f'🔍 Ищу ответ на вопрос: "{query}"...'))

        # 1. ШАГ: Поиск релевантных кусков текста (Context Retrieval)
        try:
            context_chunks = search_relevant_chunks(query, category=category, top_k=3)

            if not context_chunks:
                self.stdout.write(
                    self.style.WARNING("Ничего не найдено в базе данных.")
                )
                return

            self.stdout.write(f"✅ Найдено подходящих чанков: {len(context_chunks)}")

            # Выведем для интереса, что он нашел
            for i, chunk in enumerate(context_chunks):
                self.stdout.write(f"--- Чанк №{i + 1} ---\n{chunk.chunk_text[:100]}...")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка при поиске: {e}"))
            return

        # 2. ШАГ: Генерация ответа через GPT (Generation)
        self.stdout.write(self.style.SUCCESS("🤖 Генерирую финальный ответ..."))

        try:
            answer = generate_answer(query, context_chunks)

            self.stdout.write(self.style.NOTICE("\n" + "=" * 30))
            self.stdout.write(self.style.SUCCESS("ОТВЕТ ИИ:"))
            self.stdout.write(answer)
            self.stdout.write(self.style.NOTICE("=" * 30 + "\n"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка при генерации: {e}"))
