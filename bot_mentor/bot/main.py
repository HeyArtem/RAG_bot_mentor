import logging

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from django.conf import settings

# Импортируем роутеры (обработчики)
from bot_mentor.bot.handlers import admin_handlers, common, registration
from bot_mentor.bot.middlewares.auth import AuthMiddleware

# Настройка логов (вывод в терминал)
logging.basicConfig(level=logging.INFO)


async def start_bot_app():
    # 1. Настраиваем session для Telegram Bot API
    session = None

    if settings.TELEGRAM_PROXY_ENABLED and settings.TELEGRAM_PROXY_URL:
        logging.info(
            f"🌐 Telegram bot будет использовать proxy: {settings.TELEGRAM_PROXY_URL}"
        )
        session = AiohttpSession(proxy=settings.TELEGRAM_PROXY_URL)
    else:
        logging.info("🌐 Telegram bot запускается без proxy")

    # 2. Инициализация бота и диспетчера
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN, session=session)

    # MemoryStorage нужен для хранения состояний (FSM), например, когда ждем имя стажера
    dp = Dispatcher(storage=MemoryStorage())
    await set_commands(bot)

    # Подключаем проверку прав к роутеру
    common.router.message.middleware(AuthMiddleware())

    # 3. Подключаем роутеры (в правильном порядке!)
    dp.include_router(admin_handlers.router)  # Админка выше common
    dp.include_router(
        registration.router
    )  # регистрация должна быть выше common, чтобы перехватывать /start
    dp.include_router(common.router)

    # 4. Запуск
    try:
        logging.info("🤖 Бот запущен и готов к работе")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


async def set_commands(bot: Bot):
    """
    Подсказки команд при вводе
    """
    commands = [
        BotCommand(command="start", description="Запустить бота / Регистрация"),
        BotCommand(command="help", description="Получить справку"),
    ]
    await bot.set_my_commands(commands)
