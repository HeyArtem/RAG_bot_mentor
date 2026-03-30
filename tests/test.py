import os

import django

"""
Посмотреть содержимое таблиц в БД
"""

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bot_mentor.settings")

django.setup()
# from bot_mentor.models import Chunk

# def search_relevant_chunks(query: str, top_k: int = 12):
#     """
#     Находит наиболее релевантные чанки (куски текста) в базе данных
#     по заданному текстовому запросу.
#
#     Использует pgvector для поиска ближайших векторов.
#     """
#     # ♻️ Попытка получить ответи из БД обычным поиском
#     try:
#         print(f"♻️ type 1, ищу через __icontains. Запрос: {query}")
#         relevant_chunks = Chunk.objects.filter(chunk_text__icontains=query).order_by(
#             "document_id", "chunk_index"
#         )
#
#         #     content_chunks =" ".join(i for i in relevant_chunks)
#         #     print(f" content_chunks: {content_chunks}")
#         # return relevant_chunks
#
#     except Exception as ex:
#         print(f"🧬 Ошибка при поиске __icontains: {ex}")


# print(search_relevant_chunks(query="вишн"))
