# import os

# import django

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bot_mentor.settings")
#
# django.setup()
# from django.contrib.postgres.search import TrigramSimilarity
#
# from bot_mentor.models import Chunk
#
# user_text = "вишня"

"""
user_text = "вишн"
Выдает:  3 фрагмента
✅ И это очень точно
Недостаток в том, что он спотыкается на опечатках
"""

# qs = Chunk.objects.filter(chunk_text__icontains=user_text).order_by(
#     "document_id", "chunk_index"
# )
# show_qs = "\n\n".join(f"{i.chunk_index}\n{i.chunk_text}" for i in qs)
# print(
#     show_qs,
#     "\n\n",
#     f"👽 Количество сущностей:{len(qs)}",
# )


"""
❌ Поиск с учетом опечаток (pg_trgm)
similarity плохо работает
Я ищу по 'вишн' и жду 3 сущности (как вывел бы chunk_text__icontains)
а она выводит рябину, семгу и всякое непотребное
"""
# qs = (
#     Chunk.objects     # это вар без filter(similarity__gt=0.008) для Теста
#     .annotate(similarity=TrigramSimilarity("chunk_text", user_text))
#     .order_by("-similarity")[:10]
# )
# show_qs ="\n\n".join(f"{i.chunk_index}\n{i.chunk_text}\n{i.similarity}" for i in qs)
# print(len(qs),"\n", show_qs)

# qs = (
#     Chunk.objects
#     .annotate(similarity=TrigramSimilarity("chunk_text", user_text))
#       .filter(similarity__gt=0.009)
#       .order_by("-similarity"))
# show_qs ="\n\n".join(f"{i.chunk_index}\n{i.chunk_text}" for i in qs)
# print(len(qs),"\n", show_qs)

# qs = (
#     Chunk.objects
#     .annotate(similarity=TrigramSimilarity("chunk_text", user_text))
#       .filter(similarity__gt=0.008)
#       .order_by("document_id", "chunk_index"))
# show_qs ="\n\n".join(f"{i.chunk_index}\n{i.chunk_text}" for i in qs)
# print(show_qs, "\n\n", f"👽 Количество сущностей:{len(qs)}")
