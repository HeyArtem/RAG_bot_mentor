from aiogram import F, Router, types
from asgiref.sync import sync_to_async

from bot_mentor.models import TelegramUser

"""
Здесь все скрипты для Менеджера
"""

router = Router()


# ⚡️ Фильтр F.data.startswith позволяет ловить все нажатия, начинающиеся с approve_
@router.callback_query(F.data.startswith("approve_"))
async def approve_user(callback: types.CallbackQuery):
    """
    Менеджер одобрил заявку
    """
    # Достаем ID из callback_data (например, "approve_12345" -> 12345)
    target_user_id = int(callback.data.split("_")[1])

    # Обновляем статус в БД
    user = await sync_to_async(
        TelegramUser.objects.filter(telegram_id=target_user_id).first
    )()

    if user:
        user.is_approved = True
        await sync_to_async(user.save)()

        # Уведомляем менеджера (того, кто нажал кнопку)
        await callback.message.edit_text(
            f"✅ Пользователь {user.full_name} успешно одобрен!"
        )

        # 🚀 Уведомляем стажера, что путь открыт
        await callback.bot.send_message(
            chat_id=target_user_id,
            text="🎉 Ура! Менеджер одобрил твою заявку. Теперь ты можешь задавать вопросы по меню!",
        )

    # Обязательно отвечаем на callback, чтобы убрать "часики" на кнопке в ТГ
    await callback.answer()


@router.callback_query(F.data.startswith("decline_"))
async def decline_user(callback: types.CallbackQuery):
    """
    Менеджер отклонил заявку
    """
    target_user_id = int(callback.data.split("_")[1])

    # Находим и удаляем или помечаем как "отклонен"
    user = await sync_to_async(
        TelegramUser.objects.filter(telegram_id=target_user_id).first
    )()

    if user:
        # Вариант А: Просто удаляем из базы, чтобы мог попробовать снова
        name = user.full_name
        await sync_to_async(user.delete)()

        await callback.message.edit_text(f"❌ Заявка пользователя {name} отклонена.")

        # Уведомляем бедолагу
        await callback.bot.send_message(
            chat_id=target_user_id,
            text="К сожалению, твоя заявка на обучение отклонена. Обратись к менеджеру лично. 😔",
        )

    # ⚡️ ГАСИМ ЧАСИКИ
    await callback.answer()
