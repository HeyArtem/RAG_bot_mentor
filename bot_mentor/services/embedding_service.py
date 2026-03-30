import re
from typing import List

from django.conf import settings
from django.db import transaction
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI
from pgvector.django import CosineDistance

from bot_mentor.models import Chunk, Document
from bot_mentor.prompts import system_prompt

"""
Здесь 3 фу-ции.
-def process_document - режет на чанки и сохраняет прнумерванные куски текста
    и векторы.
-def search_relevant_chunks - находит релевантные чанки в БД
    (использует два приема поиска ответа)
-def generate_answer [! ОТКЛЮЧЕНА]  - отправка вопроса и релевантных кусков текста
    в модель "gpt-4.1-nano" получает ответ
"""

embedding_model = OpenAIEmbeddings(
    model=settings.AI_EMBEDDING_MODEL,  # 'text-embedding-3-large'
    openai_api_key=settings.AI_EMBEDDING_KEY,
    openai_api_base=settings.OPENAI_API_BASE,
    check_embedding_ctx_length=False,  # Отключаем лишние проверки токенов у langchain-openai
    chunk_size=15,  # Теперь он будет отправлять 51 чанк пачками по 15 штук.
)


def process_document(document_id: int):
    """
    Берет ID уже созданного (через админку) документа,
    читает его файл, режет на куски и сохраняет векторы.

    Важно:
    - старые UploadedFile и Document не удаляем
    - старые Chunk этой же категории удаляем только после
      успешного получения новых embeddings
    - удаление старых и создание новых Chunk выполняем атомарно
    """
    try:
        # 1. Получаем документ из базы (он уже создан админом!)
        doc = Document.objects.get(id=document_id)

        # 2. Получаем путь к файлу
        # (doc.uploaded_file — это связь, .file — это поле, .path — это путь на диске)
        file_path = doc.uploaded_file.file.path

        print(f"🚀 [Start] Обработка документа: {doc.title}")

        # 3. Проверка расширения
        if not file_path.endswith(".txt"):
            print(f"❌ Ошибка: Файл {doc.uploaded_file.file_name} не .txt. Пропускаем.")
            return

        # 4. Читаем файл
        with open(file_path, encoding="utf-8") as f:
            source_text = f.read()

        if not source_text:
            print("⚠️ Файл пустой!")
            return

        # 5. Нарезка на чанки (Chunking) по ^
        raw_chunks = [chunk for chunk in source_text.split("^") if chunk]
        print(f"🔪 Разрезали текст на {len(raw_chunks)} чанков.")

        # 6. Добавляем контекстную шапку и HTML-оформление (📖кух|menu)
        header = f"<i>📖 {doc.title} | {doc.category}</i>\n\n"

        chunks_with_context = []
        for raw_chunk in raw_chunks:
            formatted_text = (
                # Делаем жирными заголовки разделов
                raw_chunk.replace("Описание:", "<b>Описание: </b>")
                .replace("Сторителлинг:", "<b>Сторителлинг: </b>")
                .replace("Особенности:", "<b>Особенности: </b>")
            )

            # Ищем [ссылку] и превращаем в <a href="...">📸</a>
            # Это регулярное выражение ищет всё, что внутри квадратных скобок и начинается с http
            formatted_text = re.sub(
                r"\[(https?://[^\s\]]+)\]",
                r'<a href="\1">📸</a>',
                formatted_text,
            )
            chunks_with_context.append(header + formatted_text)

        # 7. Получаем embeddings
        print("📡 Отправляем запрос к ProxyAPI...")
        try:
            # Отправляем именно тексты С ШАПКОЙ
            # Мы отправляем ВСЕ тексты сразу (batch). Это в 50 раз быстрее цикла.
            vectors = embedding_model.embed_documents(chunks_with_context)
        except Exception as e:
            print(f"🔥 Ошибка при запросе к API: {e}")
            return

        # 8. Собираем новые чанки в память
        chunks_to_create = []
        # Сохранение в БД (Bulk Create)
        # Собираем объекты в список, чтобы сохранить одним SQL-запросом
        for i, (chunk_text, vector) in enumerate(zip(chunks_with_context, vectors)):
            chunks_to_create.append(
                Chunk(
                    document=doc,
                    chunk_index=i,
                    chunk_text=chunk_text,
                    embedding=vector,
                )
            )

        # 9. ЭКЗОРЦИЗМ 👻
        # Всё делаем в одной транзакции:
        # либо старые удалились и новые записались,
        # либо ничего не изменилось.
        with transaction.atomic():
            old_chunks_qs = Chunk.objects.filter(document__category=doc.category)
            old_chunks_count = old_chunks_qs.count()

            print(
                f"🕯️ Подготовка к экзорцизму: найдено {old_chunks_count} старых чанков "
                f"в категории '{doc.category}'"
            )

            old_chunks_qs.delete()
            print(f"🧹 Старые чанки категории '{doc.category}' удалены.")

            Chunk.objects.bulk_create(chunks_to_create)

        print(
            f"✅ [Success] Сохранено {len(chunks_to_create)} новых векторов "
            f"для категории '{doc.category}'."
        )

    except Document.DoesNotExist:
        print(f"❌ Документ с ID {document_id} не найден.")
    except Exception as e:
        print(f"🔥 Критическая ошибка: {e}")


def search_relevant_chunks(query: str, top_k: int = 12) -> List[Chunk]:
    """
    Извлекает из БД нужные чанки и отправляет из в ТГ-бота
    👽 Type 1 (простой, ищет прямое совпадение)
    👽 Type 2 (сложный, превращает запрос пользователя в вектор
    и ищет по косинусному расстоянию)
    """
    # --- 👽 TYPE 1: Прямое вхождение ---
    try:
        print(f"\n🧬 type 1, ищу через __icontains. Запрос: {query}\n")

        relevant_chunks = list(
            Chunk.objects.select_related("document")
            .filter(chunk_text__icontains=query)
            .order_by("document_id", "chunk_index")
        )[:top_k]

        if relevant_chunks:

            # 🧬 Моя контролька
            for i in relevant_chunks:
                print(
                    f"🧬 index:{i.chunk_index},\n text:{(i.chunk_text)[33:210]}", "\n\n"
                )

            return relevant_chunks
    except Exception as ex:
        print(f"🧬 Ошибка при поиске __icontains: {ex}")

    # --- 👽 TYPE 2: Векторный поиск (Если Type 1 ничего не нашел) ---
    print(f"\n🧬 TYPE 1 пусто. Включаю TYPE 2 (Векторы) для '{query}'...")
    try:
        # 1. Получаем вектор для запроса
        # NOTE: embed_query используется для одного запроса, embed_documents - для списка
        print(f"\n🧬 Превращаем запрос в вектор: '{query}'")
        query_vector = embedding_model.embed_query(query)
        vector_chunks = list(
            Chunk.objects.select_related("document")
            .annotate(
                # Добавляем к каждому найденному чанку метрику 'distance'
                # Чем меньше расстояние, тем лучше (ближе 0)
                distance=CosineDistance("embedding", query_vector)
            )
            .filter(distance__lt=0.67)
            .order_by("distance")[
                :top_k
            ]  # Сортируем: чем меньше расстояние, тем лучше 0,67
        )
        return vector_chunks
    except Exception as e:
        print(f"🔥Ошибка векторизации: {e}")


def generate_answer(query: str, context: List[Chunk]) -> str:
    """
    Не используется
    Генерирует финальный ответ, используя вопрос пользователя и найденный контекст.
    """
    # 1. Создаем клиент для генерации
    # Используем настройки для ProxyAPI и модели GPT-4.1-nano
    client = OpenAI(
        base_url=settings.OPENAI_API_BASE, api_key=settings.AI_COMPLETION_KEY
    )

    # 2. Собираем контекст в одну строку
    if not context:
        return (
            "Извините, я не нашел информации, которая могла бы ответить на ваш вопрос."
        )

    # Склеиваем тексты чанков, добавляя нумерацию
    context_text = ""
    for idx, c in enumerate(context):
        context_text += f"\n{idx}) {c.chunk_text}\n"

    # res = "\n\n".join(i for i in context_text)
    # print(context_text)

    # 3. Формируем промт (Prompt) - инструкция для LLM
    user_prompt = f"Контекст:\n{context_text}\n\nВопрос пользователя: {query}"

    # 4. Отправляем запрос в LLM
    print("🧠 Отправляем запрос LLM для генерации ответа...")
    try:
        response = client.chat.completions.create(
            model=settings.AI_COMPLETION_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,  # 👈 Это сделает его максимально точным и лишит фантазии
            top_p=1,
        )
        # # Хочу увидеть ответ нейронки
        # show_answer = [i for i in response]
        # print(f"♻️ Ответ нейронки:\n\n{show_answer}")

        # Эксперементально промпта с json
        list_str_chunks = (
            response.choices[0]
            .message.content.replace("[", "")
            .replace("]", "")
            .split(", ")
        )
        list_int_chunks = [int(i) for i in list_str_chunks]

        # answer = ""
        # for i in list_int_chunks:
        #     answer += "\n\n" + context[i].chunk_text

        answer = ""
        try:
            for i in list_int_chunks:
                answer += "\n\n" + context[i].chunk_text
        except IndexError:
            pass

        return answer

    except Exception as e:
        print(f"🔥 Ошибка при запросе к модели GPT: {e}")
        return "Извините, произошла ошибка связи с генеративной моделью."
