import logging
import os

from celery import Celery

logger = logging.getLogger(__name__)
# Устанавливаем настройки Django по умолчанию для Celery.
# Это нужно, чтобы Celery знало, где искать наш settings.py
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Создаем экземпляр приложения Celery.
# Имя проекта 'config' - это название нашего корневого каталога.
app = Celery("config")

# Загружаем конфигурацию из настроек Django.
# Все настройки, начинающиеся с 'CELERY_', будут использоваться.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Автоматически находим задачи в файлах tasks.py во всех приложениях Django.
# Например, в bot_mentor/tasks.py
app.autodiscover_tasks()

app.conf.timezone = "Europe/Moscow"
app.conf.enable_utc = False


# Эта функция полезна для   отладки
@app.task(bind=True)
def debug_task(self):
    """Пример тестовой задачи, чтобы проверить, что Celery работает."""
    logger.info(f"Request: {self.request!r}")
