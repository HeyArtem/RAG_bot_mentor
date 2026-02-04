import json
import os

from dotenv import load_dotenv
from openai import OpenAI

# Загружаем переменные окружения
load_dotenv()

# Создаём клиент
client = OpenAI(
    base_url="https://api.proxyapi.ru/openai/v1", api_key=os.getenv("KEY_EMBEDDING")
)

# Текст для теста
text = "Превысокомногорассмотрительствующий"

print("🔍 Делаем запрос к API...\n")

try:
    # 1. Полный response
    response = client.embeddings.create(model="text-embedding-3-small", input=text)

    # 2. Выводим структуру response (упрощённо)
    print("1. response (тип):", type(response))
    print("   Успешно! Объект создан.\n")

    # 3. response.data
    print("2. response.data (список чанков):")
    print(f"   Количество элементов: {len(response.data)}")
    for i, item in enumerate(response.data):
        print(f"   [{i}] object={item.object}, index={item.index}")
    print()

    # 4. response.data[0].embedding
    embedding = response.data[0].embedding
    print("3. response.data[0].embedding:")
    print(f"   Тип: {type(embedding)}")
    print(f"   Это список из {len(embedding)} чисел (вектор)\n")

    # 5. len(response.data[0].embedding)
    print("4. Длина вектора:", len(embedding))

    # 6. Первые 5 чисел
    print("5. Первые 5 чисел:", embedding[:5])

    # 7. Сохраняем полный ответ в JSON
    response_dict = response.model_dump()  # ← преобразуем в словарь
    with open("response_debug.json", "w", encoding="utf-8") as f:
        json.dump(response_dict, f, ensure_ascii=False, indent=4)
    print("\n✅ Полный ответ сохранён в 'response_debug.json'")

except Exception as e:
    print(f"❌ Ошибка: {e}")
