import os
from pathlib import Path

from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Django
SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG") == "True"
ALLOWED_HOSTS = ["*"]  # Пока разрешаем всем (для тестов)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Сторонние библиотеки
    "django_celery_results",  # Чтобы видеть результаты задач Celery
    "pgvector.django",
    "django.contrib.postgres",  # Поиск с учетом опечаток (pg_trgm)
    # Наши приложения
    "bot_mentor",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


MEDIA_URL = "/media/"
# MEDIA_URL
# URL-префикс для доступа к пользовательским загруженным файлам

MEDIA_ROOT = BASE_DIR / "media"
# MEDIA_ROOT
# путь на диске, куда Django будет сохранять загруженные файлы

STATIC_URL = "/static/"
# STATIC_URL
# URL-префикс для статики

STATIC_ROOT = BASE_DIR / "staticfiles"
# STATIC_ROOT
# папка, куда collectstatic соберет всю статику для prod/Gunicorn/Nginx

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True


STATIC_URL = "/static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==============================
# 🚀 CELERY & REDIS SETTINGS (Настраиваем асинхронность)
# ==============================
# Адрес Redis (брокер сообщений)
# CELERY_BROKER_URL = "redis://localhost:6379/0"  # Адрес нашего Redis в режиме debug
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
# CELERY_BROKER_URL из env, а если env нет — локальная разработка через localhost
CELERY_RESULT_BACKEND = "django-db"  # Результаты храним в базе Django
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE  # Celery живет в том же часовом поясе, что и Django

# ==============================
# 🤖 AI & PROXY SETTINGS
# ==============================
OPENAI_API_BASE = os.getenv("URL_API")  # Наш прокси-адрес
AI_EMBEDDING_KEY = os.getenv("KEY_EMBEDDING")
AI_EMBEDDING_MODEL = os.getenv("MODEL_EMBEDDING")

# AI_EMBEDDING_KEY = print("🧬 Обращение к модели эмбедингов")
# AI_EMBEDDING_MODEL = 0

# AI_COMPLETION_KEY = os.getenv("KEY_COMPLETION")
# AI_COMPLETION_MODEL = os.getenv("MODEL_COMPLETION")


TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN")

# Временно
MANAGER_TELEGRAM_ID = os.getenv("MANAGER_TELEGRAM_ID")

# Подключаю proxy для работы телеграмма, т.к. глцшат (работает только при вкл hiddify)
TELEGRAM_PROXY_URL = os.getenv("TELEGRAM_PROXY_URL", "")
TELEGRAM_PROXY_ENABLED = os.getenv("TELEGRAM_PROXY_ENABLED", "False") == "True"
