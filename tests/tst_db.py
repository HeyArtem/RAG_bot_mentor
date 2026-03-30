# import os
#
# import django

# from config import settings

# """
# Посмотреть содержимое таблиц в БД
# """
#
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bot_mentor.settings")
#
# django.setup()
# from bot_mentor.models import Chunk

# for i in Chunk.objects.all():
#     print(f"id:{i.id} index:{i.chunk_index} document:{i.document}\n💊chunk_text:\n {i.chunk_text}\n♻️embedding:\n{i.embedding}\n{' * ' * 20}")


# print(Chunk.objects.values("id", "content")[:5])
#
# for row in Chunk.objects.values("id", "content")[:5]:
#     print(row)


# print(list(Chunk.objects.all()))

# for row in Chunk.objects.values('id', 'chunk_index', 'document', 'chunk_text', 'embedding'):
#     print(row)


# s_db = Chunk.objects.all()

# Первые 50 символов
# s_db_clear = "\n\n".join(
#     f"id:{i.id} text:{i.chunk_text[:100]}…" for i in s_db
# )
# print(s_db_clear)


# def show_db():
#     s_db = Chunk.objects.all()
#     # квадратные скобки создают list (! список целиком в памяти), а круглые — generator
#     # s_db_clear = "\n\n".join([str(i.id) for i in s_db])
#     s_db_clear = "\n\n".join((str(i.id) for i in s_db)) #Лениво создаёт элементы при итерации, не хранит их все сразу в памяти
#     print(s_db_clear)
#
# print(show_db())


"""
💊 Если я не знаю, какие есть поля
vars(i) → словарь {имя_атрибута: значение}
Это динамически, не нужно знать заранее поля
"""
# s_db = Chunk.objects.all()
# for i in s_db:
#     # vars(i) возвращает dict всех атрибутов объекта
#     attrs = vars(i)
#     print("\n".join(f"{k}: {v}" for k, v in attrs.items()))
#     print("*"*20)

# s_db = Chunk.objects.all()
# s_db_clear = "\n\n".join(
#     "\n".join(f"{k}: {v}" for k, v in vars(i).items()) + "\n" + "*" * 20 for i in s_db
# )
#
# print(s_db_clear)
