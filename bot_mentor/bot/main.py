import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from django.conf import settings

# Импортируем роутеры (обработчики)
from bot_mentor.bot.handlers import admin_handlers, common, registration

# Настройка логов (вывод в терминал)
logging.basicConfig(level=logging.INFO)


async def start_bot_app():
    # 1. Инициализация бота и диспетчера
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

    # MemoryStorage нужен для хранения состояний (FSM), например, когда ждем имя стажера
    dp = Dispatcher(storage=MemoryStorage())
    await set_commands(bot)

    # 2. Подключаем роутеры (в правильном порядке!)
    dp.include_router(
        registration.router
    )  # регистрация должна быть выше common, чтобы перехватывать /start
    dp.include_router(admin_handlers.router)  # Админка выше common
    dp.include_router(common.router)

    # 3. Запуск
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
