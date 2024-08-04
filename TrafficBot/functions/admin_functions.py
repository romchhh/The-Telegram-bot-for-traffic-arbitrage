from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
from datetime import datetime, timedelta


def admin_create_categories_keyboard(categories_with_counts, user_id):
    keyboard = InlineKeyboardMarkup(row_width=2)
    for category, count in categories_with_counts:
        button_text = f"{category} ({count})"
        keyboard.insert(InlineKeyboardButton(text=button_text, callback_data=f"admincategory_{category}"))
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="admin_channel_statistic"))
    return keyboard


def admin_create_nonactive_categories_keyboard(categories_with_counts, user_id):
    keyboard = InlineKeyboardMarkup(row_width=2)
    for category, count in categories_with_counts:
        button_text = f"{category} ({count})"
        keyboard.insert(InlineKeyboardButton(text=button_text, callback_data=f"admincategorynon_{category}"))
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="admin_channel_statistic"))
    return keyboard
