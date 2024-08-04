from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.exceptions import ChatNotFound
from main import bot, dp
from data.config import channel_id, administrators, logs
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher import FSMContext

import asyncio
from keyboards.user_keyboards import get_start_keyboard
from keyboards.admin_keyboards import category_keyboard, get_admin_keyboard, payment_type_keyboard, cancel_keyboard, get_active_or_nonactive, get_back_keyboard, get_preview_markup
from database.admin_db import add_channel, get_active_users_count, get_users_count, get_all_user_ids, set_offer_inactive, add_quantity_to_offer
from filters.filters import IsAdmin
from states.admin_states import AddChannel, BroadcastState, AddOfferState
from functions.admin_functions import admin_create_categories_keyboard, admin_create_nonactive_categories_keyboard
from database.user_db import get_categories_from_db, fetch_offers_by_category, fetch_offer_details, get_nonactive_categories_from_db, fetch_inactive_offers_by_category

import re

from aiogram.dispatcher.filters import Text
from database.user_db import get_user_data, update_user_balance

async def check(call: types.CallbackQuery):
    user = call.from_user
    markup = InlineKeyboardMarkup(row_width=1)
    try:
        ch_name = await bot.get_chat(channel_id)
        ch_link = ch_name.invite_link
        ch_name = ch_name.title
        button = InlineKeyboardButton(text=f'{ch_name}', url=ch_link)
        markup.add(button)
        user_status = await bot.get_chat_member(chat_id=channel_id, user_id=user.id)
    except ChatNotFound:
        for x in administrators:
            await bot.send_message(x, f'Бот видалений з каналу.')
        return

    markup.add(InlineKeyboardButton(text='Підписався', callback_data='check'))
    message_text = f"Щоб отримати доступ до функцій бота, <b>потрібно підписатися на канал:</b>"

    if user_status.status == 'left':
        message_text = '❌ Ви не підписані!'
        await call.answer(message_text, show_alert=True)
        await call.message.edit_text(message_text, reply_markup=markup, disable_web_page_preview=True)
    else:
        message_text = '<b>✅ Успішно</b>'
        await call.message.edit_text(message_text)
        await asyncio.sleep(2) 
        await call.message.edit_text("Головне меню:", reply_markup=get_start_keyboard())
        
        
@dp.callback_query_handler(IsAdmin(), text='admin_channel_statistic')
async def channels_statistic_handler(callback_query: CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    keyboard = get_active_or_nonactive
    await callback_query.message.edit_text(
        "Оберіть тематику за якою бажаєте отримати статистику",
        reply_markup=keyboard
    )
    
@dp.callback_query_handler(IsAdmin(), text='admin_active_channels')
async def channels_statistic_handler(callback_query: CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    categories_with_counts = get_categories_from_db()
    keyboard = admin_create_categories_keyboard(categories_with_counts, callback_query.from_user.id)

    await callback_query.message.edit_text(
        "Оберіть тематику за якою бажаєте отримати статистику",
        reply_markup=keyboard
    )
    
@dp.callback_query_handler(lambda c: c.data.startswith('admincategory_'))
async def handle_category_selection(callback_query: CallbackQuery):
    category = callback_query.data.split("admincategory_")[1]
    offers = fetch_offers_by_category(category)

    if not offers:
        await callback_query.message.edit_text("Немає оферів для обраної категорії.")
        return

    offer_buttons = [
        InlineKeyboardButton(text=offer['channel_name'], callback_data=f"adminoffer_{offer['id']}")
        for offer in offers
    ]

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(*offer_buttons)
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="admin_active_channels"))

    await callback_query.message.edit_text(
        "Оберіть офер для перегляду деталей.",
        reply_markup=keyboard
    )
    
@dp.callback_query_handler(lambda c: c.data.startswith('adminoffer_'))
async def handle_offer_selection(callback_query: CallbackQuery):
    offer_id = int(callback_query.data.split("adminoffer_")[1])

    offer = fetch_offer_details(offer_id)

    if not offer:
        await callback_query.message.edit_text("Офер не знайдено.")
        return

    user_id = callback_query.from_user.id
    channel_id = offer['channel_id']

    remaining_orders = offer['order'] - offer['came']
    
    payed = offer['came'] * offer['payment']
    payed = round(payed, 2)

    message_text = (
        f"✅Активний офер: <a href='{offer['channel_link']}'>{offer['channel_name']}</a>\n"
        f"Тематика: {offer['category']}\n"
        f"ID: {offer['id']}\n\n"
        f"Залишилось замовлень: {offer['came']}/{offer['order']}\n\n" 
        f"Нараховано: {payed}₴\n"
        f"Оплата: {offer['payment']}₴\n"
        f"Тип оплати: {offer['payment_type']}\n\n"
        f"Коментар замовника: \n{offer['comentary']}\n\n"

    )

    add_offers_button = InlineKeyboardButton(text="Додати кількість оферів", callback_data=f"adminaddoffer_{offer['id']}")
    delete_button = InlineKeyboardButton(text="Видалити офер", callback_data=f"admindeleteoffer_{offer['id']}")
    back_button = InlineKeyboardButton(text="Назад", callback_data=f"admin_active_channels")

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(add_offers_button, delete_button, back_button)
    await callback_query.message.edit_text(message_text, reply_markup=keyboard, parse_mode="HTML", 
            disable_web_page_preview=True)
    
    
@dp.callback_query_handler(lambda c: c.data.startswith('adminaddoffer_'))
async def add_offer_callback(callback_query: CallbackQuery, state: FSMContext):
    offer_id = int(callback_query.data.split("adminaddoffer_")[1])

    await state.update_data(offer_id=offer_id)
    await AddOfferState.waiting_for_quantity.set()

    back_button = InlineKeyboardButton(text="Назад", callback_data="cancel_add_offer")

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(back_button)
    
    await callback_query.message.edit_text("Введіть кількість оферів, яку бажаєте додати (ціле число):", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == "cancel_add_offer", state=AddOfferState.waiting_for_quantity)
async def cancel_add_offer(callback_query: CallbackQuery, state: FSMContext):
    await state.finish()
    await callback_query.message.edit_text("Дію скасовано.")
    await asyncio.sleep(1)
    admin_keyboard = get_admin_keyboard()
    await callback_query.message.edit_text("Адмін панель", reply_markup=admin_keyboard)

@dp.message_handler(state=AddOfferState.waiting_for_quantity)
async def process_offer_quantity(message: types.Message, state: FSMContext):
    try:
        quantity = int(message.text)
    except ValueError:
        await message.reply("Будь ласка, введіть коректне ціле число.")
        return

    data = await state.get_data()
    offer_id = data['offer_id']

    # Update the database
    add_quantity_to_offer(offer_id, quantity)

    await bot.send_message(message.chat.id, f"Додано {quantity} оферів до офера ID: {offer_id}.")

    await state.finish()
    await asyncio.sleep(1)
    
    admin_keyboard = get_admin_keyboard()
    await bot.send_message(message.chat.id, "Адмін панель", reply_markup=admin_keyboard)
    
@dp.callback_query_handler(lambda c: c.data.startswith('admindeleteoffer_'))
async def confirm_delete_offer(callback_query: CallbackQuery):
    offer_id = int(callback_query.data.split("admindeleteoffer_")[1])
    offer = fetch_offer_details(offer_id)

    if not offer:
        await callback_query.message.edit_text("Офер не знайдено.")
        return

    confirm_keyboard = InlineKeyboardMarkup(row_width=2)
    confirm_keyboard.add(
        InlineKeyboardButton(text="Так", callback_data=f"confirmdeleteoffer_{offer_id}"),
        InlineKeyboardButton(text="Ні", callback_data=f"adminoffer_{offer_id}")
    )

    await callback_query.message.edit_text(
        "Ви впевнені, що хочете видалити цей офер?",
        reply_markup=confirm_keyboard
    )

@dp.callback_query_handler(lambda c: c.data.startswith('confirmdeleteoffer_'))
async def handle_delete_offer(callback_query: CallbackQuery):
    offer_id = int(callback_query.data.split("confirmdeleteoffer_")[1])
    offer = fetch_offer_details(offer_id)

    if not offer:
        await callback_query.message.edit_text("Офер не знайдено.")
        return

    # Update the 'active' column to 0 in the 'channels' table
    set_offer_inactive(offer_id)

    await callback_query.message.edit_text("Офер було успішно видалено.")
    
@dp.callback_query_handler(IsAdmin(), text='admin_nonactive_channels')
async def channels_statistic_handler(callback_query: CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    categories_with_counts = get_nonactive_categories_from_db()
    keyboard = admin_create_nonactive_categories_keyboard(categories_with_counts, callback_query.from_user.id)

    await callback_query.message.edit_text(
        "Оберіть тематику за якою бажаєте отримати статистику",
        reply_markup=keyboard
    )
    
@dp.callback_query_handler(lambda c: c.data.startswith('admincategorynon_'))
async def handle_category_selection(callback_query: CallbackQuery):
    category = callback_query.data.split("admincategorynon_")[1]
    offers = fetch_inactive_offers_by_category(category)

    if not offers:
        await callback_query.message.edit_text("Немає оферів для обраної категорії.")
        return

    offer_buttons = [
        InlineKeyboardButton(text=offer['channel_name'], callback_data=f"adminoffernon_{offer['id']}")
        for offer in offers
    ]

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(*offer_buttons)
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="admin_nonactive_channels"))

    await callback_query.message.edit_text(
        "Оберіть офер для перегляду деталей.",
        reply_markup=keyboard
    )
    
@dp.callback_query_handler(lambda c: c.data.startswith('adminoffernon_'))
async def handle_offer_selection(callback_query: CallbackQuery):
    offer_id = int(callback_query.data.split("adminoffernon_")[1])

    offer = fetch_offer_details(offer_id)

    if not offer:
        await callback_query.message.edit_text("Офер не знайдено.")
        return

    user_id = callback_query.from_user.id
    channel_id = offer['channel_id']

    remaining_orders = offer['order'] - offer['came']
    
    payed = offer['came'] * offer['payment']
    payed = round(payed, 2)

    message_text = (
        f"❌Неактивний офер: <a href='{offer['channel_link']}'>{offer['channel_name']}</a>\n"
        f"Тематика: {offer['category']}\n"
        f"ID: {offer['id']}\n\n"
        f"Виконано: {offer['came']}/{offer['order']}\n\n" 
        f"Нараховано: {payed}₴\n"
        f"Оплата: {offer['payment']}₴\n"
        f"Тип оплати: {offer['payment_type']}\n\n"
        f"Коментар замовника: \n{offer['comentary']}\n\n"

    )

    back_button = InlineKeyboardButton(text="Назад", callback_data=f"admin_nonactive_channels")

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(back_button)
    await callback_query.message.edit_text(message_text, reply_markup=keyboard, parse_mode="HTML")
    
    
@dp.callback_query_handler(IsAdmin(), text='user_statistic')
async def statistic_handler(callback_query: CallbackQuery):
    total_users = get_users_count()
    active_users = get_active_users_count()

    response_message = (
            f"👥 Загальна кількість користувачів: {total_users}\n"
            f"📱 Кількість активних користувачів: {active_users}\n"
        )
    
    keyboard = get_back_keyboard()
    await callback_query.message.edit_text(response_message, reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query_handler(IsAdmin(), Text(startswith='mailing'))
async def send_broadcast_prompt(call: CallbackQuery):
    # await call.message.answer(
    #     'Текст розсилки підтримує розмітку *HTML*, тобто:\n\n'
    #     '<b>*Жирний*</b> - <b>Приклад: Жирний текст</b>\n'
    #     '<i>_Курсив_</i> - <i>Приклад: Курсивний текст</i>\n'
    #     '<pre>`Моноширний`</pre> - <pre>Приклад: Моноширний текст</pre>\n'
    #     '<a href="https://www.telegrambotsfromroman.com/">[Обернути текст у посилання](https://www.telegrambotsfromroman.com/)</a> - '
    #     '<a href="https://www.telegrambotsfromroman.com/">Приклад: Обернутий текст у посилання</a>',
    #     parse_mode="HTML"
    # )
    await call.message.answer("Введіть текст повідомлення або натисніть /skip, щоб пропустити:")
    await BroadcastState.text.set()

@dp.message_handler(state=BroadcastState.text)
async def process_broadcast_text(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['text'] = message.text
    await message.answer("Надішліть фото для додавання до повідомлення або натисніть /skip, щоб пропустити:")
    await BroadcastState.photo.set()

@dp.message_handler(content_types=['photo'], state=BroadcastState.photo)
async def process_broadcast_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['photo'] = message.photo[0].file_id
    await send_preview(message.chat.id, data, state)
    await BroadcastState.preview.set()

async def send_preview(chat_id, data, state: FSMContext):
    markup = get_preview_markup()
    text = "📣 *Попередній перегляд розсилки:*\n\n"
    text += data.get('text', '')

    if 'photo' in data and data['photo'] is not None:
        await bot.send_photo(chat_id, data['photo'], caption=text, parse_mode="Markdown", reply_markup=markup)
    else:
        await bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)

    async with state.proxy() as stored_data:
        stored_data.update(data)

@dp.callback_query_handler(text="send_broadcast", state=BroadcastState.preview)
async def send_broadcast_to_users_callback(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text = data.get('text', '')
    photo = data.get('photo')
    await send_broadcast_to_users(text, photo, call.message.chat.id)
    await call.answer()
    await state.finish()

@dp.message_handler(commands=['skip'], state=[BroadcastState.text, BroadcastState.photo])
async def skip_step(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if 'text' not in data:
            data['text'] = None
        if 'photo' not in data:
            data['photo'] = None
    await send_preview(message.chat.id, data, state)
    if 'text' in data and 'photo' in data:
        await BroadcastState.preview.set()
    elif 'text' in data:
        await BroadcastState.photo.set()
    else:
        await BroadcastState.text.set()

async def send_broadcast_to_users(text, photo, chat_id):
    try:
        user_ids = get_all_user_ids()
        for user_id in user_ids:
            if text.strip():
                try:
                    if photo:
                        await bot.send_photo(user_id, photo, caption=text, parse_mode='HTML')
                    else:
                        await bot.send_message(user_id, text, parse_mode='HTML')
                except Exception as e:
                    print(f"Помилка відправлення повідомлення користувачу з ID {user_id}: {str(e)}")

        await bot.send_message(chat_id, f"Розсилка успішно виконана для {len(user_ids)} користувачів.")
        admin_keyboard = get_admin_keyboard()
        await bot.send_message(chat_id, "Адмін панель", reply_markup=admin_keyboard)
    except Exception as e:
        await bot.send_message(chat_id, f"Виникла помилка: {str(e)}")
        

@dp.callback_query_handler(text="cancel_broadcast", state=BroadcastState.preview)
async def cancel_broadcast_callback(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    await state.finish()
    await call.message.answer("Розсилка відмінена.")
    admin_keyboard = get_admin_keyboard()
    await bot.send_message(user_id, "Адмін панель", reply_markup=admin_keyboard)
    await call.answer()

@dp.callback_query_handler(lambda c: IsAdmin(), text_startswith='add_channel')
async def add_channel_handler(call: types.CallbackQuery):
    await call.message.answer("Щоб бот міг збирати статистику, він має бути адміністратором на каналі. \nВведіть назву канала:", reply_markup=cancel_keyboard)
    await AddChannel.waiting_for_name.set()

@dp.message_handler(state=AddChannel.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    if message.text.lower() == "скасувати":
        await message.answer("Додавання каналу скасовано.", reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
        admin_keyboard = get_admin_keyboard()
        await message.answer("Адмін панель", reply_markup=admin_keyboard)
        return

    if not message.text:
        await message.answer("Будь ласка, введіть назву канала.")
        return

    await state.update_data(channel_name=message.text)
    data = await state.get_data()
    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id - 1,
            text=f"Назва канала: {data['channel_name']}\n\nВведіть силку на канал:",
            reply_markup=cancel_keyboard
        )
    except Exception as e:
        await message.answer(f"Назва канала: {data['channel_name']}\n\nВведіть силку на канал:", reply_markup=cancel_keyboard)
    await AddChannel.waiting_for_link.set()

@dp.message_handler(state=AddChannel.waiting_for_link)
async def process_link(message: types.Message, state: FSMContext):
    if message.text.lower() == "скасувати":
        await message.answer("Додавання каналу скасовано.", reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
        admin_keyboard = get_admin_keyboard()
        await message.answer("Адмін панель", reply_markup=admin_keyboard)
        return

    if not message.text:
        await message.answer("Будь ласка, введіть силку на канал.")
        return

    await state.update_data(channel_link=message.text)
    data = await state.get_data()
    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id - 1,
            text=f"Назва канала: {data['channel_name']}\nСилка на канал: {data['channel_link']}\n\nВведіть ID каналу:",
            reply_markup=cancel_keyboard
        )
    except Exception as e:
        await message.answer(f"Назва канала: {data['channel_name']}\nСилка на канал: {data['channel_link']}\n\nВведіть ID каналу:", reply_markup=cancel_keyboard)
    await AddChannel.waiting_for_id.set()

@dp.message_handler(state=AddChannel.waiting_for_id)
async def process_id(message: types.Message, state: FSMContext):
    if message.text.lower() == "скасувати":
        await message.answer("Додавання каналу скасовано.", reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
        admin_keyboard = get_admin_keyboard()
        await message.answer("Адмін панель", reply_markup=admin_keyboard)
        return

    if not re.match(r'^-?\d+(\.\d+)?$', message.text):
        await message.answer("Будь ласка, введіть число.")
        return

    await state.update_data(channel_id=message.text)
    data = await state.get_data()
    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id - 1,
            text=f"Назва канала: {data['channel_name']}\nСилка на канал: {data['channel_link']}\nID каналу: {data['channel_id']}\n\nОберіть категорію:",
            reply_markup=category_keyboard
        )
    except Exception as e:
        await message.answer(f"Назва канала: {data['channel_name']}\nСилка на канал: {data['channel_link']}\nID каналу: {data['channel_id']}\n\nОберіть категорію:", reply_markup=category_keyboard)
    await AddChannel.waiting_for_category.set()

@dp.callback_query_handler(state=AddChannel.waiting_for_category)
async def process_category(call: types.CallbackQuery, state: FSMContext):
    if call.data == "cancel":
        await call.message.answer("Додавання каналу скасовано.", reply_markup=types.ReplyKeyboardRemove())
        admin_keyboard = get_admin_keyboard()
        await call.message.answer("Адмін панель", reply_markup=admin_keyboard)
        await state.finish()
        return

    if 'category_' not in call.data:
        await call.message.answer("Помилка: невірний формат даних.", reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
        return

    categories = {
        "sport": "Спорт",
        "work": "Робота",
        "cooking": "Кулінарія",
        "news": "Новини",
        "transport": "Транспорт",
        "motivation": "Мотивація",
        "auto": "Авто",
        "cinema": "Кіно",
        "afishes": "Афіши",
        "crypta": "Крипта",
        "english": "Англійська"
    }

    category_key = call.data.split('category_')[1]
    category = categories.get(category_key, "Unknown")
    await state.update_data(category=category)
    data = await state.get_data()
    try:
        await call.message.edit_text(
            text=f"Назва канала: {data['channel_name']}\nСилка на канал: {data['channel_link']}\nID каналу: {data['channel_id']}\nКатегорія: {data['category']}\n\nВведіть оплату за підписку:",
            reply_markup=cancel_keyboard
        )
    except Exception as e:
        await call.message.answer(f"Назва канала: {data['channel_name']}\nСилка на канал: {data['channel_link']}\nID каналу: {data['channel_id']}\nКатегорія: {data['category']}\n\nВведіть оплату за підписку:", reply_markup=cancel_keyboard)
    await AddChannel.waiting_for_payment.set()

@dp.message_handler(state=AddChannel.waiting_for_payment)
async def process_payment(message: types.Message, state: FSMContext):
    if message.text.lower() == "скасувати":
        await message.answer("Додавання каналу скасовано.", reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
        admin_keyboard = get_admin_keyboard()
        await message.answer("Адмін панель", reply_markup=admin_keyboard)
        return

    if not re.match(r'^\d+(\.\d+)?$', message.text):
        await message.answer("Будь ласка, введіть число.")
        return

    await state.update_data(payment=message.text)
    data = await state.get_data()
    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id - 1,
            text=f"Назва канала: {data['channel_name']}\nСилка на канал: {data['channel_link']}\nID каналу: {data['channel_id']}\nКатегорія: {data['category']}\nОплата: {data['payment']}\n\nВведіть бажану кількість замовлень:",
            reply_markup=cancel_keyboard
        )
    except Exception as e:
        await message.answer(f"Назва канала: {data['channel_name']}\nСилка на канал: {data['channel_link']}\nID каналу: {data['channel_id']}\nКатегорія: {data['category']}\nОплата: {data['payment']}\n\nВведіть бажану кількість замовлень:", reply_markup=cancel_keyboard)
    await AddChannel.waiting_for_order.set()

@dp.message_handler(state=AddChannel.waiting_for_order)
async def process_order(message: types.Message, state: FSMContext):
    if message.text.lower() == "скасувати":
        await message.answer("Додавання каналу скасовано.", reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
        admin_keyboard = get_admin_keyboard()
        await message.answer("Адмін панель", reply_markup=admin_keyboard)
        return

    if not message.text.isdigit():
        await message.answer("Будь ласка, введіть число.")
        return

    await state.update_data(order=message.text)
    data = await state.get_data()
    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id - 1,
            text=f"Назва канала: {data['channel_name']}\nСилка на канал: {data['channel_link']}\nID каналу: {data['channel_id']}\nКатегорія: {data['category']}\nОплата: {data['payment']}\nЗамовлення: {data['order']}\n\nОберіть тип оплати:",
            reply_markup=payment_type_keyboard
        )
    except Exception as e:
        await message.answer(f"Назва канала: {data['channel_name']}\nСилка на канал: {data['channel_link']}\nID каналу: {data['channel_id']}\nКатегорія: {data['category']}\nОплата: {data['payment']}\nЗамовлення: {data['order']}\n\nОберіть тип оплати:", reply_markup=payment_type_keyboard)
    await AddChannel.waiting_for_payment_type.set()

@dp.callback_query_handler(state=AddChannel.waiting_for_payment_type)
async def process_payment_type(call: types.CallbackQuery, state: FSMContext):
    if call.data == "cancel":
        await call.message.answer("Додавання каналу скасовано.", reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
        admin_keyboard = get_admin_keyboard()
        await call.message.answer("Адмін панель", reply_markup=admin_keyboard)
        return

    if 'payment_' not in call.data:
        await call.message.answer("Помилка: невірний формат даних.", reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
        return

    payment_types = {
        "application": "Заявка"
    }

    payment_key = call.data.split('payment_')[1]
    payment_type = payment_types.get(payment_key, "Unknown")
    await state.update_data(payment_type=payment_type)
    data = await state.get_data()
    try:
        await call.message.edit_text(
            text=f"Назва канала: {data['channel_name']}\nСилка на канал: {data['channel_link']}\nID каналу: {data['channel_id']}\nКатегорія: {data['category']}\nОплата: {data['payment']}\nЗамовлення: {data['order']}\nТип оплати: {data['payment_type']}\n\nВведіть коментар від замовника:",
            reply_markup=cancel_keyboard
        )
    except Exception as e:
        await call.message.answer(f"Назва канала: {data['channel_name']}\nСилка на канал: {data['channel_link']}\nID каналу: {data['channel_id']}\nКатегорія: {data['category']}\nОплата: {data['payment']}\nЗамовлення: {data['order']}\nТип оплати: {data['payment_type']}\n\nВведіть коментар від замовника:", reply_markup=cancel_keyboard)
    await AddChannel.waiting_for_commentary.set()

@dp.message_handler(state=AddChannel.waiting_for_commentary)
async def process_commentary(message: types.Message, state: FSMContext):
    if message.text.lower() == "скасувати":
        await message.answer("Додавання каналу скасовано.", reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
        admin_keyboard = get_admin_keyboard()
        await message.answer("Адмін панель", reply_markup=admin_keyboard)
        return

    await state.update_data(commentary=message.text)
    data = await state.get_data()
    review_text = (
        f"Офер: {data['channel_name']} ({data['channel_link']})\n"
        f"Тематика: {data['category'].capitalize()}\n"
        f"ID каналу: {data['channel_id']}\n"
        f"Замовлення: {data['order']}\n"
        f"Оплата: {data['payment']}₴\n"
        f"Тип оплати: З\n"
        f"Коментар замовника:\n{data['commentary']}\n\n"
        f"Заборонено: накрутка, мотивований трафік.\n\n"
        f"Все вірно?"
    )
    await message.answer(review_text, reply_markup=InlineKeyboardMarkup().add(
        InlineKeyboardButton("Так", callback_data="confirm_yes"),
        InlineKeyboardButton("Ні", callback_data="confirm_no")
    ))
    await AddChannel.confirm.set()

@dp.callback_query_handler(state=AddChannel.confirm, text='confirm_yes')
async def process_confirmation(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    add_channel(data['channel_name'], data['channel_link'], data['channel_id'], data['category'], data['payment'], data['order'], data['payment_type'], data['commentary'])

    await call.message.delete()
    await call.message.answer("Канал успішно доданий до оферів.", reply_markup=types.ReplyKeyboardRemove())
    await state.finish()

    admin_keyboard = get_admin_keyboard()
    await call.message.answer("Адмін панель", reply_markup=admin_keyboard)

@dp.callback_query_handler(state=AddChannel.confirm, text='confirm_no')
async def process_cancellation(call: types.CallbackQuery, state: FSMContext):

    await call.message.delete()
    await call.message.answer("Додавання каналу скасовано.", reply_markup=types.ReplyKeyboardRemove())
    await state.finish()
    admin_keyboard = get_admin_keyboard()
    await call.message.answer("Адмін панель", reply_markup=admin_keyboard)


@dp.callback_query_handler(text_startswith="confirm_payout_")
async def handle_confirm_payout(callback_query: CallbackQuery):
    user_id = int(callback_query.data.split("_")[-1])
    user = get_user_data(user_id)

    if user:
        balance = user[3]
        referral_id = user[7] 

        await bot.send_message(
            user_id, 
            "Ваш запит на виплату підтверджено. Очікуйте на переказ протягом кількох хвилин."
        )

        update_user_balance(user_id, -balance)

        if referral_id:
            referral_bonus = balance * 0.05
            update_user_balance(referral_id, referral_bonus)
            
            await bot.send_message(
                referral_id,
                f"Вам було нараховано {referral_bonus:.2f}₴ за активність вашого реферала."
            )
            
            await bot.send_message(
                logs,
                f"Виплату {balance}₴ для користувача ID {user_id} підтверджено. Нараховано {referral_bonus:.2f}₴ рефералу ID {referral_id}."
            )
        else:
            await bot.send_message(
                logs,
                f"Виплату для користувача ID {user_id} підтверджено."
            )

        await bot.edit_message_reply_markup(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            reply_markup=InlineKeyboardMarkup() 
        )
    
    else:
        await bot.answer_callback_query(callback_query.id, text="Користувача не знайдено")



@dp.callback_query_handler(text_startswith="cancel_payout_")
async def handle_cancel_payout(callback_query: CallbackQuery):
    user_id = int(callback_query.data.split("_")[-1])
    await bot.send_message(
        user_id,
        "Ваш запит на виплату відхилено."
    )
    await bot.send_message(
        logs,
        f"Запит на виплату для користувача з ID {user_id} був скасований."
    )
    await bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=InlineKeyboardMarkup()
    )

        
@dp.callback_query_handler(text="adminback")
async def handle_back(callback_query: CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    admin_keyboard = get_admin_keyboard()
    await callback_query.message.edit_text("Адмін панель", reply_markup=admin_keyboard)
    
def register_admin_callbacks(dp: Dispatcher):
    dp.register_callback_query_handler(check, lambda c: c.data == 'check')