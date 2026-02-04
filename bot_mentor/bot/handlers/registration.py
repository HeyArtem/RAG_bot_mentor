from aiogram import Router, types
from aiogram.filters import Command as CommandFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asgiref.sync import sync_to_async
from django.conf import settings  # ⚡️ Импортируем настройки

from bot_mentor.bot.keyboards import get_approval_keyboard  # Импорт кнопок
from bot_mentor.models import TelegramUser

"""
Содержит логику знакомства.
Бот использует FSM (Finite State Machine — Конечный автомат),
чтобы вести стажера по шагам: «Как зовут?» -> «Запомнил, жди одобрения».
"""

router = Router()


class RegState(StatesGroup):
    waiting_for_name = State()


@router.message(CommandFilter("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    # Проверяем, есть ли юзер в базе
    user = await sync_to_async(
        TelegramUser.objects.filter(telegram_id=message.from_user.id).first
    )()

    if not user:
        await message.answer(
            "Добро пожаловать в систему обучения! ✨\nПожалуйста, введи свои Фамилию и Имя:"
        )
        await state.set_state(RegState.waiting_for_name)
    elif not user.is_approved:
        await message.answer(
            "Твоя заявка всё еще на рассмотрении. Менеджер скоро её одобрит! ⏳"
        )
    else:
        await message.answer(
            f"Привет, {user.full_name}! Я готов отвечать на вопросы. Что хочешь узнать?"
        )


@router.message(CommandFilter("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "📖 **Справка по боту:**\n\n"
        "1. Просто пиши вопросы по меню (например: 'что входит в сет Юрьев-Польский?').\n"
        "2. Если ты менеджер — ты будешь получать уведомления о новых стажерах.\n"
        "3. `/start` — перезагрузить бота."
    )


@router.message(RegState.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    full_name = message.text
    user_id = message.from_user.id

    # # Создаем юзера в БД
    # new_user = await sync_to_async(TelegramUser.objects.create)(
    #     telegram_id=user_id,
    #     username=message.from_user.username,
    #     full_name=full_name,
    #     role="trainee",
    # )

    await message.answer("Заявка отправлена менеджеру! Жди уведомления. ⏳")

    # ⚡️ МАГИЯ: Отправляем сообщение менеджеру
    if settings.MANAGER_TELEGRAM_ID:
        try:
            await message.bot.send_message(
                chat_id=settings.MANAGER_TELEGRAM_ID,
                text=f"🚀 Новая заявка на обучение!\nИмя: {full_name}\nID: {user_id}",
                reply_markup=get_approval_keyboard(user_id),  # Цепляем кнопки
            )
        except Exception as e:
            print(f"Ошибка отправки менеджеру: {e}")

    await state.clear()
