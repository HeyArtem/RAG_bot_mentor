from django.conf import settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI

from bot_mentor.models import Chunk, Document, UploadedFile


def get_embedding(text: str) -> list[float]:
    """
    Делает запрос к API, возвращает векторное представление (эмбеддинг) для переданного текста.
    Параметры:
        text (str): Текст, для которого требуется получить эмбеддинг.
    Возвращает:
        list[float]: Список чисел с плавающей точкой — вектор эмбеддинга.
    """
    client = OpenAI(base_url=settings.URL_API, api_key=settings.KEY_EMBEDDING)

    response = client.embeddings.create(model=settings.MODEL_EMBEDDING, input=text)
    return response.data[0].embedding


def save_document_with_chunks(
    title: str, category: str, file_path: str, file_name: str
):
    """
    Полностью обрабатывает файл: читает, рубит на чанки, создаёт эмбеддинги, сохраняет в БД.
    """
    # 1. Сохраняем метаинформацию о файле
    uploaded_file = UploadedFile.objects.create(
        file_name=file_name, file_path=file_path
    )

    document = Document.objects.create(
        title=title, category=category, uploaded_file=uploaded_file
    )

    # 2. Читаем файл
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # 3. Режем на чанки
    # chunk_size=1000-Максимальное количество токенов (или символов) в одном чанке.
    # chunk_overlap=100 количество символов "перекрытия" между чанками.
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = splitter.split_text(content)

    # 4. Обрабатываем каждый чанк
    for i, text in enumerate(texts):
        vector = get_embedding(text)
        Chunk.objects.create(
            document=document, chunk_index=i, chunk_text=text, embedding=vector
        )

    print(f"✅ Документ '{title}' обработан и сохранён")


def search(query: str, top_k: int = 5) -> list:
    """
    Ищет наиболее релевантные документы по векторному запросу.
    Параметры:
        query (str): Текстовый запрос, по которому выполняется поиск.
        top_k (int): Сколько наиболее подходящих результатов вернуть (по умолчанию 5).
    Возвращает:
        list: Список найденных документов с их оценками похожести.
    """
    ...
