from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_approval_keyboard(user_id: int) -> InlineKeyboardMarkup:
    # ⚡️ Используем Builder для создания кнопок
    builder = InlineKeyboardBuilder()

    # callback_data — это то, что прилетит нам в бот при нажатии
    builder.add(
        InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{user_id}")
    )
    builder.add(
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"decline_{user_id}")
    )

    return builder.as_markup()
