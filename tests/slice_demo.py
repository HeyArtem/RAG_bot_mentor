# text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234"
# MAX_LENGTH = 5
#
# print(f"Исходный текст: {text}")
# print(f"Длина текста: {len(text)}")
# print(f"Размер одного куска: {MAX_LENGTH}")
# print("-" * 40)
#
# for i in range(0, len(text), MAX_LENGTH):
#     chunk = text[i : i + MAX_LENGTH]
#     print(f"i = {i:2} -> text[{i}:{i + MAX_LENGTH}] -> {chunk}")


# for i in range(0, 10, -1):
#     print(i)


# numbers = range(10)
# print(numbers)          # range(0, 5)
# print(numbers[0])       # 2
# print(numbers[2:8])     # range(2, 5)
# print(list(numbers[2:8]))     # range(2, 5)


# text = "кот пес лиса"
# print(text.rfind("|"))  # -1


# У rfind есть диапазон поиска Можно искать не по всей строке, а только в куске:
text = "aa|bb|cc|dd"
print(text.rfind("|", 0, 6))  # 5
