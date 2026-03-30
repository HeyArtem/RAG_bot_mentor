FROM python:3.12-slim

# Отключаем создание .pyc и буферизацию stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Рабочая директория внутри контейнера
WORKDIR /app

# Системные пакеты:
# build-essential / gcc — на случай сборки некоторых Python-пакетов
# libpq-dev — клиентские библиотеки PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Сначала копируем только requirements, чтобы лучше кэшировались зависимости
COPY requirements.txt /app/

# Устанавливаем Python-зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . /app/

# Создаем папки для статики и медиа
RUN mkdir -p /app/staticfiles /app/media

# Порт приложения внутри контейнера
EXPOSE 8000
