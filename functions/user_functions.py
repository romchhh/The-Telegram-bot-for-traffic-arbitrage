from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
from datetime import datetime, timedelta
from functions.translate import translate_text

user_link_requests = {} 
LINKS_PER_MINUTE = 5
REQUEST_INTERVAL = timedelta(minutes=1)


def create_categories_keyboard(categories_with_counts, user_id):
    keyboard = InlineKeyboardMarkup(row_width=2)
    for category, count in categories_with_counts:
        button_text = f"{translate_text(category, user_id)} ({count})"
        keyboard.insert(InlineKeyboardButton(text=button_text, callback_data=f"category_{category}"))
    keyboard.add(InlineKeyboardButton(text=translate_text("Назад", user_id), callback_data="back"))
    return keyboard



def format_records(records):
    messages = []
    for record in records:
        channel_name, channel_link, category, channel_id, order, payment, payment_type, commentary = record
        message = (
            f"Офер: {channel_name} ({channel_link})\n"
            f"Тематика: {category}\n"
            f"ID: {channel_id}\n"
            f"Залишилось замовлення: {order}\n"
            f"Оплата: {payment:.2f}₴\n"
            f"Тип оплати: {payment_type}\n\n"
            f"Коментар замовника:\n{commentary}"
        )
        messages.append(message)
    return messages

def cleanup_requests():
    now = datetime.now()
    for user_id, timestamps in list(user_link_requests.items()):
        user_link_requests[user_id] = [ts for ts in timestamps if now - ts < REQUEST_INTERVAL]
        if not user_link_requests[user_id]:
            del user_link_requests[user_id]

# Function to check if a user is within the rate limit
def can_send_link(user_id):
    cleanup_requests()
    if user_id not in user_link_requests:
        user_link_requests[user_id] = []
    timestamps = user_link_requests[user_id]
    if len(timestamps) < LINKS_PER_MINUTE:
        timestamps.append(datetime.now())
        return True
    return False

def get_channels_keyboard(channels):
    keyboard = InlineKeyboardMarkup(row_width=2)  # Устанавливаем ширину строки в 2 кнопки
    for channel in channels:
        keyboard.insert(InlineKeyboardButton(text=channel, callback_data=f"channel_{channel}"))
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="back"))
    return keyboard