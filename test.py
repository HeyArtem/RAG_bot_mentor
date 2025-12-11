import os

import requests
from dotenv import load_dotenv

load_dotenv()

keys_list = ["KEY_EMBEDDING", "KEY_COMPLETION"]

url = "https://api.proxyapi.ru/proxyapi/balance"

try:
    for key_item in keys_list:
        value = os.getenv(key_item)

        headers = {"Authorization": f"Bearer {value}"}

        response = requests.get(url, headers=headers)

        # ✅ Сначала проверяем статус
        if response.status_code != 200:
            print(f"❌ Ошибка: {response.status_code}")
            print(f"[!]: {response.text}")
            exit()

        # ✅ Теперь парсим JSON
        data = response.json()

        # ✅ Используем .get() и сохраняем результат
        balance = data.get("balance", "неизвестно")

        # ✅ Выводим
        print(f"✅ Баланс {key_item}: {balance} ₽")


# 🛑 Конкретные исключения
except requests.exceptions.RequestException as e:
    print(f"🌐 Ошибка сети: {e}")
except requests.exceptions.JSONDecodeError:
    print(f"📦 Не удалось распарсить JSON. Ответ: {response.text}")


# keys_list = ['KEY_EMBEDDING', 'KEY_COMPLETION']
# url = "https://api.proxyapi.ru/proxyapi/balance"  # ✅ Без пробелов!
#
# for key_item in keys_list:
#     value = os.getenv(key_item)
#     if not value:
#         print(f"🔑 Не найден ключ: {key_item}")
#         continue
#
#     headers = {"Authorization": f"Bearer {value}"}
#     response = None  # ← Объявляем заранее
#
#     try:
#         response = requests.get(url, headers=headers)
#
#         if response.status_code != 200:
#             print(f"❌ Ошибка {key_item}: {response.status_code}")
#             print(f"[!]: {response.text}")
#             continue  # exit() прервёт весь цикл, а мы хотим проверить оба ключа
#
#         data = response.json()
#         balance = data.get('balance', 'неизвестно')
#         print(f"✅ Баланс {key_item}: {balance} ₽")
#
#     except requests.exceptions.RequestException as e:
#         print(f"🌐 Ошибка сети ({key_item}): {e}")
#     except requests.exceptions.JSONDecodeError:
#         if response:
#             print(f"📦 Не JSON ({key_item}): {response.text}")
#         else:
#             print(f"📦 Не удалось получить ответ ({key_item})")
