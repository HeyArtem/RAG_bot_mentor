from typing import List

from django.conf import settings
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from openai import OpenAI
from pgvector.django import CosineDistance

from bot_mentor.models import Chunk, Document
from bot_mentor.prompts import system_prompt

"""
Здесь 3 фу-ции.
-def process_document - режет на чанки и сохраняет прнумерванные куски текста
    и векторы.
-def search_relevant_chunks - находит релевантные чанки в БД
-def generate_answer - отправка вопроса и релевантных кусков текста
    в модель "gpt-4.1-nano" получает ответ
"""

embedding_model = OpenAIEmbeddings(
    model=settings.AI_EMBEDDING_MODEL,  # 'text-embedding-3-small'
    openai_api_key=settings.AI_EMBEDDING_KEY,
    openai_api_base=settings.OPENAI_API_BASE,
    check_embedding_ctx_length=False,  # Отключаем лишние проверки токенов у langchain-openai
    chunk_size=15,  # Теперь он будет отправлять 51 чанк пачками по 15 штук.
)


def process_document(document_id: int):
    """
    Берет ID уже созданного (через админку) документа,
    читает его файл, режет на куски и сохраняет векторы.
    """
    try:
        # 1. Получаем документ из базы (он уже создан админом!)
        doc = Document.objects.get(id=document_id)

        # Получаем полный путь к файлу на диске
        # (doc.uploaded_file — это связь, .file — это поле, .path — это путь на диске)
        file_path = doc.uploaded_file.file.path

        print(f"🚀 [Start] Обработка документа: {doc.title}")

        # 2. Проверка и чтение файла
        if not file_path.endswith(".txt"):
            print(f"❌ Ошибка: Файл {doc.uploaded_file.file_name} не .txt. Пропускаем.")
            return

        with open(file_path, encoding="utf-8") as f:
            text = f.read()

        if not text:
            print("⚠️ Файл пустой!")
            return

        # 3. Нарезка на Чанки (Chunking)
        # (Разделители по приоритету. Сначала ищем 4 переноса (конец сета), потом 2 (конец блюда))
        # 1000 символов размер, 150 символов перехлест (чтобы не рвать предложения)
        text_splitter = CharacterTextSplitter(
            separator="^",
            chunk_size=1,
            chunk_overlap=0,
            is_separator_regex=False,
        )

        # Режем текст на «сырые» куски
        raw_chunks = text_splitter.split_text(text)
        print(f"🔪 Разрезали текст на {len(raw_chunks)} чанков.")

        # 4. Добавление "Контекстной шапки"
        # Чтобы в каждом куске ИИ видел, к чему относится текст
        header = f"Источник: {doc.title} (Категория: {doc.category})\n\n"

        # Создаем финальные тексты для векторизации
        chunks_with_context = [header + chunk for chunk in raw_chunks]

        # 5. Векторизация-Embeddings (Batch запрос)
        print("📡 Отправляем запрос к ProxyAPI...")
        try:
            # Отправляем именно тексты С ШАПКОЙ
            # Мы отправляем ВСЕ тексты сразу (batch). Это в 50 раз быстрее цикла.
            vectors = embedding_model.embed_documents(chunks_with_context)
        except Exception as e:
            print(f"🔥 Ошибка при запросе к API: {e}")
            return

        # 6. Сохранение в БД (Bulk Create)
        # Собираем объекты в список, чтобы сохранить одним SQL-запросом
        chunks_to_create = []
        for i, (chunk_text, vector) in enumerate(zip(chunks_with_context, vectors)):
            chunks_to_create.append(
                Chunk(
                    document=doc,
                    chunk_index=i,
                    chunk_text=chunk_text,  # Сохраняем текст с шапкой
                    embedding=vector,
                )
            )

        # Удаляем старые чанки этого документа, если они были (защита от дублей)
        Chunk.objects.filter(document=doc).delete()

        # bulk_create - «супер-сохранение» в Django.
        # Вместо того чтобы делать 100 запросов к базе (сохранять каждый чанк отдельно),
        # Django делает один мощный запрос, отправляя в базу сразу всю пачку данных.
        # Это в десятки раз быстрее.
        Chunk.objects.bulk_create(chunks_to_create)
        print(f"✅ [Success] Сохранено {len(chunks_to_create)} векторов в базу.")

    except Document.DoesNotExist:
        print(f"❌ Документ с ID {document_id} не найден.")
    except Exception as e:
        print(f"🔥 Критическая ошибка: {e}")


# Мы уже инициализировали: embedding_model, который делал векторы для документов.
# Теперь он будет делать вектор для вопроса!


def search_relevant_chunks(query: str, category: str, top_k: int = 15) -> List[Chunk]:
    """
    Находит наиболее релевантные чанки (куски текста) в базе данных
    по заданному текстовому запросу.

    Использует pgvector для поиска ближайших векторов.
    """
    print(f"📡 Превращаем запрос в вектор: '{query}'")

    try:
        # 1. Получаем вектор для запроса
        # NOTE: embed_query используется для одного запроса, embed_documents - для списка
        query_vector = embedding_model.embed_query(query)
    except Exception as e:
        print(f"🔥 Ошибка при создании вектора запроса: {e}")
        return []

    # 2. Формируем запрос к базе данных
    # Оператор '<=>' в pgvector - это оператор косинусного расстояния (близости)
    # Мы ищем 'top_k' чанков, которые максимально близки к вектору запроса.

    # 3. Фильтруем по категории (важно!)
    # Ищем только среди документов, принадлежащих нужной категории (например, 'menu')
    relevant_chunks = (
        Chunk.objects.filter(
            document__category=category,  # Фильтр по полю category в связанной модели Document
        )
        .annotate(
            # Добавляем к каждому найденному чанку метрику 'distance'
            # Чем меньше расстояние, тем лучше (ближе 0)
            distance=CosineDistance("embedding", query_vector)
        )
        .order_by("distance")[:top_k]  # Сортируем: чем меньше расстояние, тем лучше
    )  # Ограничиваем количество результатов (по умолчанию 5)

    print(f"🔎 Найдено {len(relevant_chunks)} релевантных чанков.")
    return list(relevant_chunks)


def generate_answer(query: str, context: List[Chunk]) -> str:
    """
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
    context_text = "\n---\n".join([c.chunk_text for c in context])

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
        )
        return response.choices[0].message.content

    except Exception as e:
        print(f"🔥 Ошибка при запросе к модели GPT: {e}")
        return "Извините, произошла ошибка связи с генеративной моделью."
