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
