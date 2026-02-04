import asyncio

from django.core.management.base import BaseCommand

from bot_mentor.bot.main import start_bot_app  # Импортируем из новой папки


class Command(BaseCommand):
    help = "Запуск бота наставника"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("🚀 Бот запускается через новую структуру...")
        )
        asyncio.run(start_bot_app())
