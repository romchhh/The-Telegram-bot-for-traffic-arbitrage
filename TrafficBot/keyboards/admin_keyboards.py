from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, KeyboardButton, ContentTypes, ReplyKeyboardMarkup, \
    InputFile


def get_admin_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton(text="Статистика по юзерах", callback_data='user_statistic'),
        InlineKeyboardButton(text="Статистика по каналах", callback_data='admin_channel_statistic'),
        InlineKeyboardButton(text="Розсилка", callback_data='mailing'),
        InlineKeyboardButton(text="Додати канал", callback_data='add_channel')
    ]
    
    keyboard.add(*buttons)
    
    return keyboard



category_keyboard = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("Спорт", callback_data="category_sport"),
    InlineKeyboardButton("Робота", callback_data="category_work"),
    InlineKeyboardButton("Кулінарія", callback_data="category_cooking"),
    InlineKeyboardButton("Новини", callback_data="category_news"),
    InlineKeyboardButton("Транспорт", callback_data="category_transport"),
    InlineKeyboardButton("Мотивація", callback_data="category_motivation"),
    InlineKeyboardButton("Авто", callback_data="category_auto"),
    InlineKeyboardButton("Кіно", callback_data="category_cinema"),
    InlineKeyboardButton("Афіши", callback_data="category_afishes"),
    InlineKeyboardButton("Крипта", callback_data="category_crypta"),
    InlineKeyboardButton("Англійська", callback_data="category_english")

)


payment_type_keyboard = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton("Заявка", callback_data="payment_application")
)


cancel_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("Скасувати")
)

get_active_or_nonactive= InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton("Активні офери", callback_data='admin_active_channels'),
    InlineKeyboardButton("Неактивні офери", callback_data='admin_nonactive_channels'),
    InlineKeyboardButton("Назад", callback_data='adminback')
    
)


def get_back_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    back_button = InlineKeyboardButton("Назад", callback_data="adminback")
    keyboard.add(back_button)
    return keyboard


def get_preview_markup():
    markup = InlineKeyboardMarkup()
    preview_button = InlineKeyboardButton("📤 Надіслати", callback_data="send_broadcast")
    cancel_button = InlineKeyboardButton("❌ Відміна", callback_data="cancel_broadcast")
    markup.row(preview_button, cancel_button)
    markup.one_time_keyboard = True
    return markup
