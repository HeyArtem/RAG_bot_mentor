from celery import shared_task
from django.core.files.storage import default_storage
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .models import Chunk, Document
from .services.embedding_service import get_embedding


@shared_task
def process_document(document_id):
    try:
        doc = Document.objects.get(id=document_id)
        file_path = default_storage.path(doc.uploaded_file.file_path)

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Разбиваем на чанки
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        texts = splitter.split_text(content)

        # Удаляем старые чанки
        Chunk.objects.filter(document=doc).delete()

        # Обрабатываем каждый чанк
        for i, text in enumerate(texts):
            vector = get_embedding(text)
            Chunk.objects.create(
                document=doc, chunk_index=i, chunk_text=text, embedding=vector
            )

        print(f"✅ Документ '{doc.title}' обработан")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        raise
