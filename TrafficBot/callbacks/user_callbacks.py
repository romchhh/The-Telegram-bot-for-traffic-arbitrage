from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ParseMode
from aiogram.dispatcher.filters import BoundFilter
from aiogram.utils.exceptions import ChatNotFound
from main import bot, dp
from data.config import channel_id, administrators
from aiogram.dispatcher import Dispatcher
from datetime import datetime, timedelta
import time
from aiogram.dispatcher import FSMContext
from aiogram.contrib.middlewares.fsm import FSMContext
import asyncio
from data.config import logs

from filters.filters import IsSubscribed, IsPrivate
from states.user_states import CardState

from keyboards.user_keyboards import get_start_keyboard, get_back_keyboard, get_payment_keyboard, get_back, get_back_statystic, get_comunity_keyboard, get_lang_keyboard
from functions.user_functions import create_categories_keyboard, format_records, can_send_link, get_channels_keyboard
from database.user_db import *
from functions.translate import translate_text

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

    markup.add(InlineKeyboardButton(text=translate_text('Підписався', user.id), callback_data='check'))
    message_text = translate_text("Щоб отримати доступ до функцій бота, <b>потрібно підписатися на канал:</b>", user.id)

    if user_status.status == 'left':
        message_text = translate_text('❌ Ви не підписані!', user.id)
        await call.answer(message_text, show_alert=True)
        await call.message.edit_text(message_text, reply_markup=markup, disable_web_page_preview=True)
    else:
        message_text = translate_text('<b>✅ Успішно</b>', user.id)
        await call.message.edit_text(message_text)
        await asyncio.sleep(2)
        await call.message.edit_text(translate_text("Головне меню:", user.id), reply_markup=get_start_keyboard(user.id))

@dp.callback_query_handler(IsSubscribed(), text="ofers")
async def handle_ofers(callback_query: CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    categories_with_counts = get_categories_from_db()
    keyboard = create_categories_keyboard(categories_with_counts, callback_query.from_user.id)

    await callback_query.message.edit_text(
        translate_text("Оберіть тематику з якою бажаєте працювати.\nВи можете працювати одразу з декількома тематиками і різними каналами в одній тематиці.", callback_query.from_user.id),
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data.startswith('category_'))
async def handle_category_selection(callback_query: CallbackQuery):
    category = callback_query.data.split("category_")[1]
    offers = fetch_offers_by_category(category)

    if not offers:
        await callback_query.message.edit_text(translate_text("Немає оферів для обраної категорії.", callback_query.from_user.id))
        return

    offer_buttons = [
        InlineKeyboardButton(text=offer['channel_name'], callback_data=f"offer_{offer['id']}")
        for offer in offers
    ]

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(*offer_buttons)
    keyboard.add(InlineKeyboardButton(text=translate_text("Назад", callback_query.from_user.id), callback_data="ofers"))

    await callback_query.message.edit_text(
        translate_text("Оберіть офер для перегляду деталей.", callback_query.from_user.id),
        reply_markup=keyboard
    )


@dp.callback_query_handler(lambda c: c.data.startswith('offer_'))
async def handle_offer_selection(callback_query: CallbackQuery):
    offer_id = int(callback_query.data.split("offer_")[1])

    offer = fetch_offer_details(offer_id)

    if not offer:
        await callback_query.message.edit_text(translate_text("Офер не знайдено.", callback_query.from_user.id))
        return

    user_id = callback_query.from_user.id
    channel_id = offer['channel_id']

    links = get_links_for_user(user_id, channel_id)
    links_text = "\n".join([f"{i + 1}. <code>{link}</code> ({used})" for i, (link, used) in enumerate(links)])

    remaining_orders = offer['order'] - offer['came']

    message_text = (
        f"{translate_text('Офер:', user_id)} <a href='{offer['channel_link']}'>{offer['channel_name']}</a>\n"
        f"{translate_text('Тематика:', user_id)} {offer['category']}\n"
        f"ID: {offer['id']}\n\n"
        f"{translate_text('Залишилось замовлень:', user_id)} {remaining_orders}\n\n"  # Display remaining orders
        f"{translate_text('Оплата:', user_id)} {offer['payment']}₴\n"
        f"{translate_text('Тип оплати:', user_id)} {offer['payment_type']}\n\n"
        f"{translate_text('Коментар замовника:', user_id)}\n{offer['comentary']}\n\n"
        f"{translate_text('Ваше(i) посилання:', user_id)}\n{links_text}"
    )

    back_button = InlineKeyboardButton(text=translate_text("Назад", callback_query.from_user.id), callback_data=f"ofers")
    get_link_button = InlineKeyboardButton(text=translate_text("Отримати посилання", callback_query.from_user.id), callback_data=f"get_link_{offer['id']}")

    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(get_link_button, back_button)
    await callback_query.message.edit_text(message_text, reply_markup=keyboard, parse_mode="HTML", 
            disable_web_page_preview=True)


@dp.callback_query_handler(lambda c: c.data.startswith('get_link_'))
async def handle_get_link(callback_query: CallbackQuery):
    offer_id = int(callback_query.data.split("get_link_")[1])
    offer = fetch_offer_details(offer_id)
    user_id = callback_query.from_user.id

    if not offer:
        await callback_query.message.edit_text(translate_text("Офер не знайдено.", callback_query.from_user.id))
        return

    chat_id = offer['channel_id']

    remaining_orders = offer['order'] - offer['came']

    if not can_send_link(callback_query.from_user.id):
        text = translate_text("Ви перевищили ліміт запитів. Спробуйте знову пізніше.", callback_query.from_user.id)
        await bot.answer_callback_query(
            callback_query_id=callback_query.id,
            text=text,
            show_alert=True
        )
        return

    try:
        user_status = await bot.get_chat_member(chat_id=chat_id, user_id=callback_query.from_user.id)
        invite_link = await bot.create_chat_invite_link(
            chat_id=chat_id,
            creates_join_request=True
        )

        add_link(invite_link.invite_link, chat_id, user_id, offer['channel_name'], offer['payment'])
        links = get_links_for_user(user_id, chat_id)
        links_text = "\n".join([f"{i + 1}. <code>{link}</code> ({used})" for i, (link, used) in enumerate(links)])

        message_text = (
            f"{translate_text('Офер:', user_id)} <a href='{offer['channel_link']}'>{offer['channel_name']}</a>\n"
            f"{translate_text('Тематика:', user_id)} {offer['category']}\n"
            f"ID: {offer['id']}\n\n"
            f"{translate_text('Залишилось замовлень:', user_id)} {remaining_orders}\n\n" 
            f"{translate_text('Оплата:', user_id)} {offer['payment']}₴\n"
            f"{translate_text('Тип оплати:', user_id)} {offer['payment_type']}\n\n"
            f"{translate_text('Коментар замовника:', user_id)}\n{offer['comentary']}\n\n"
            f"{translate_text('Ваше(i) посилання:', user_id)}\n{links_text}"
        )

        await callback_query.message.edit_text(
            message_text, 
            reply_markup=callback_query.message.reply_markup, 
            parse_mode='HTML', 
            disable_web_page_preview=True
        )
    except Exception as e:
        await callback_query.message.edit_text(translate_text(f"Помилка при створенні посилання для чату ID {chat_id}: {e}", callback_query.from_user.id))


@dp.callback_query_handler(IsSubscribed(), text="statystic")
async def handle_statystic(callback_query: CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    channels = get_user_channels(user_id)
    if channels:
        keyboard = get_channels_keyboard(channels)
        await callback_query.message.edit_text(translate_text("Оберіть офер.", user_id), reply_markup=keyboard)
    else:
        await callback_query.message.edit_text(translate_text("У вас немає згенерованих силок для каналів.", user_id), reply_markup=get_back_keyboard(user_id))



@dp.callback_query_handler(lambda c: c.data.startswith('channel_'))
async def handle_channel(callback_query: CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    channel_name = callback_query.data.split('_')[1]
    channel_stats = get_channel_statistics(user_id, channel_name)
    if channel_stats:
        text = (
            f"<b>{channel_stats['channel_name']}</b>\n\n"
            f"<b>{translate_text('Дохід:', user_id)}</b> {channel_stats['total_payment']}₴\n"
            f"<b>{translate_text('Запрошено:', user_id)}</b> {channel_stats['total_used']}\n\n"
            f"<b>{translate_text('Посилання:', user_id)}</b>\n{channel_stats['links_list']}"
        )
        await callback_query.message.edit_text(text, reply_markup=get_back_statystic(user_id), parse_mode='HTML')
    else:
        await callback_query.message.edit_text(
            translate_text("Статистика для цього каналу не знайдена.", user_id),
            reply_markup=get_back_statystic(user_id),
            parse_mode='HTML'
        )




@dp.callback_query_handler(IsSubscribed(), text="payment")
async def handle_payment(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user = get_user_data(user_id)

    if user:
        balance = user[3]
        ofers = user[4]
        card = user[5]

        min_payout_amount = 500

        if card:
            card_str = str(card)
            formatted_card = f"{card_str[:4]}********{card_str[-4:]}"
            card_info = translate_text(f"Прив'язана картка: `{formatted_card}`", user_id)
        else:
            card_info = translate_text("Ви ще не додали жодного способу виплати.", user_id)

        message_text = (
            f"{translate_text('Ваш баланс:', user_id)} {balance}₴\n"
            f"{translate_text('Мінімальна сума для виплати:', user_id)} {min_payout_amount}₴\n\n"
            f"{card_info}"
        )
        keyboard = get_payment_keyboard(user_id)
        await bot.answer_callback_query(callback_query.id)
        await callback_query.message.edit_text(message_text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await bot.answer_callback_query(callback_query.id, text=translate_text("User not found", user_id))



@dp.callback_query_handler(IsSubscribed(), text="link_card")
async def handle_link_card(callback_query: CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    await callback_query.message.edit_text(translate_text("Будь ласка, введіть номер вашої картки (16 цифр):", callback_query.from_user.id), reply_markup=get_back(user_id))
    await CardState.waiting_for_card.set()

@dp.message_handler(state=CardState.waiting_for_card)
async def process_card_number(message: types.Message, state: FSMContext):
    card_number = message.text.strip()

    if len(card_number) == 16 and card_number.isdigit():
        user_id = message.from_user.id
        update_user_card(user_id, card_number)
        await message.answer(translate_text("Ваша картка успішно прив'язана!", user_id))
        await asyncio.sleep(2)
        await message.answer(translate_text("Головне меню:", user_id), reply_markup=get_start_keyboard(user_id))
    else:
        await message.answer(translate_text("Невірний номер картки. Будь ласка, введіть номер картки (16 цифр):", user_id))
        return
    await state.finish()



@dp.callback_query_handler(IsSubscribed(), text="request_payout")
async def handle_request_payout(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user = get_user_data(user_id)

    if user:
        balance = user[3]
        if balance >= 500:
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                InlineKeyboardButton(translate_text("Підтвердити ✅", user_id), callback_data=f"confirm_request_{user_id}"),
                InlineKeyboardButton(translate_text("Назад", user_id), callback_data="payment")
            )
            await callback_query.message.edit_text(translate_text("Ви впевнені, що хочете зробити запит на виплату?", user_id), reply_markup=keyboard)
        else:
            text = translate_text("Ваш баланс менше мінімальної суми для виплати.", user_id)
            await bot.answer_callback_query(
                callback_query_id=callback_query.id,
                text=text,
                show_alert=True
            )
            return
    else:
        await bot.answer_callback_query(callback_query.id, text=translate_text("User not found", user_id))



@dp.callback_query_handler(IsSubscribed(), text_startswith="confirm_request_")
async def handle_confirm_request(callback_query: CallbackQuery):
    user_id = int(callback_query.data.split("_")[-1])
    user = get_user_data(user_id)

    if user:
        balance = user[3]
        ofers = user[4]
        card = user[5]  # No need to escape Markdown for inline code

        user_info = (
            f"Користувач попросив виплату:\n"
            f"ID: {user_id}\n"
            f"Username: @{callback_query.from_user.username}\n"
            f"Баланс: {balance}₴\n"
            f"Кількість приведених підписників: {ofers}\n"
            f"Карта: `{card}`\n"  # Format card details as inline code
        )
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("Підтвердити", callback_data=f"confirm_payout_{user_id}"),
            InlineKeyboardButton("Скасувати", callback_data=f"cancel_payout_{user_id}")
        )
        await bot.send_message(logs, user_info, reply_markup=keyboard, parse_mode="Markdown")
        await callback_query.message.edit_text("Ваш запит на виплату надіслано адміністратору.")
        await asyncio.sleep(2) 
        await callback_query.message.edit_text("Головне меню:", reply_markup=get_start_keyboard(user.id))
    else:
        await bot.answer_callback_query(callback_query.id, text="User not found")



@dp.callback_query_handler(IsSubscribed(), text="comunity")
async def handle_comunity(callback_query: CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    user_id = callback_query.from_user.id
    text = "Усі новини, інструкції та актуальні канали платформи Traffic Community⚡️ за посиланнями."
    translated_text = translate_text(text, user_id)

    await callback_query.message.edit_text(translated_text, reply_markup=get_comunity_keyboard(user_id))



@dp.callback_query_handler(IsSubscribed(), text="settings")
async def handle_settings(callback_query: CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    user_id = callback_query.from_user.id
    language_keyboard = get_lang_keyboard(user_id)
    await callback_query.message.edit_text(
        translate_text("Оберіть мову інтерфейса:", user_id),
        reply_markup=language_keyboard
    )

@dp.callback_query_handler(lambda c: c.data.startswith("set_lang_"))
async def handle_language_selection(callback_query: CallbackQuery):
    lang = callback_query.data.split("_")[2]
    user_id = callback_query.from_user.id

    update_user_language(user_id, lang)

    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_text(translate_text(f"Ви обрали мову: {'Українська' if lang == 'uk' else 'Англійська'}", user_id))
    await asyncio.sleep(2)
    await callback_query.message.edit_text(translate_text("Головне меню:", user_id), reply_markup=get_start_keyboard(user_id))



@dp.callback_query_handler(IsSubscribed(), text="refferal_system")
async def refferal_system(callback_query: CallbackQuery):
    user = callback_query.from_user
    username = await bot.get_me()
    referrals_count = get_referrals_count(user.id)

    text = (
        '<b>Реферальна програма</b>\n\n'
        'Запрошуйте друзів і отримуйте 5% від доходу ваших рефералів.'
        '\n\n🔗 <i>Твоє реферальне посилання:</i>'
        ' <code>t.me/{}?start={}</code>\n\n'
        '👥 <i>Кількість запрошених рефералів:</i> <b>{}</b>'.format(
            username['username'],
            user.id,
            referrals_count
        )
    )

    translated_text = translate_text(text, user.id)

    await callback_query.message.edit_text(translated_text, parse_mode='HTML',
        reply_markup=get_back_keyboard(user.id))


@dp.callback_query_handler(text="back")
async def handle_back(callback_query: CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    await callback_query.message.edit_text(translate_text("Головне меню:", user_id), reply_markup=get_start_keyboard(user_id))



@dp.callback_query_handler(IsSubscribed(), text="backck", state=CardState.waiting_for_card)
async def handle_back(callback_query: CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await state.finish()
    await handle_payment(callback_query)
    
    
def register_callbacks(dp: Dispatcher):
    dp.register_callback_query_handler(check, lambda c: c.data == 'check')

