import os

import django

# Настройка окружения Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

# noqa: E402 это комент, что бы flake8 не ругался на импорт в средине
from bot_mentor.services.embedding_service import embedding_model  # noqa: E402

try:
    print("📡 Тестируем отправку одного маленького вектора...")
    test_vector = embedding_model.embed_query("Привет, это тестовый запрос")
    print(f"✅ Успех! Получен вектор длиной: {len(test_vector)}")
except Exception as e:
    print(f"❌ Ошибка даже на одном запросе: {e}")
