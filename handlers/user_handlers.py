from main import bot, dp
from data.config import logs
from filters.filters import *

import os
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, KeyboardButton, ContentTypes, ReplyKeyboardMarkup, \
    InputFile

from aiogram.types import ChatMemberUpdated, ChatMember, ChatJoinRequest
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from keyboards.user_keyboards import get_start_keyboard
from keyboards.admin_keyboards import get_admin_keyboard
from database.user_db import *
from functions.translate import translate_text

html = 'HTML'

async def antiflood(*args, **kwargs):
    m = args[0]
    await m.answer("Не поспішай :)")

async def on_startup(dp):
    # await scheduler_jobs()
    from handlers.user_handlers import dp as user_dp
    from callbacks.user_callbacks import register_callbacks
    from callbacks.admin_callbacks import register_admin_callbacks
    register_callbacks(dp)
    register_admin_callbacks(dp)
    me = await bot.get_me()
    # await bot.send_message(logs, f"Бот @{me.username} запущений!")

async def on_shutdown(dp):
    me = await bot.get_me()
    await bot.send_message(logs, f'Bot: @{me.username} зупинений!')

@dp.message_handler(IsPrivate(), commands=["start"])
@dp.throttled(antiflood, rate=1)
async def start(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name

    user = message.from_user
    keyboard = get_start_keyboard(user_id)
    
    ref = 0

    if len(message.text) > 6:
        try:
            int(message.text.split()[1])
            ref = message.text.split()[1]
        except ValueError:
            pass

    if not check_user(user.id):
        greeting_message = translate_text(f"Привіт, {user.username}! \nГоловне меню:", user_id)
        add_user(user_id, user_name, ref)
        await message.answer(greeting_message, reply_markup=keyboard)
        if ref != 0:
            if ref:
                create_table()
                add_user(user_id, user_name, ref)
                await bot.send_message(ref, f'👤 Ви запросили <a href="tg://user?id={user.id}"><b>{user.first_name}</b></a> тепер ви отримаєте 5% від доходу вашого реферала.')
            else:
                print(f"Referral user with ID {ref} not found.")
                
    else:
        add_user(user_id, user_name, ref)
        greeting_message = translate_text(f"Привіт, {user.username}! \nГоловне меню:", user_id)
        await message.answer(greeting_message, reply_markup=keyboard)
    
@dp.chat_join_request_handler()
async def handle_join_request(join_request: ChatJoinRequest):
    user = join_request.from_user
    invite_link = join_request.invite_link
    print(f"Заявка на вступ до каналу від користувача {user.username} ({user.id})")
    print(f"Посилання: {invite_link.invite_link}")

    channel_id = get_channel_id_by_link(invite_link.invite_link)
    if channel_id:
        if is_user_in_came_users(channel_id, user.id):
            print(f"Користувач {user.id} вже є в came_users каналу {channel_id}. Пропуск запису.")
        else:
            await update_link_and_channel(invite_link.invite_link)
            sender_user_id = get_user_id_by_link(invite_link.invite_link)
            if sender_user_id:
                add_ofer_user(sender_user_id)
                payment = get_payment_by_channel_id(channel_id)
                if payment:
                    update_user_balance(sender_user_id, payment)
                add_user_to_came_users(channel_id, user.id)
                



    

@dp.message_handler(IsPrivate(), commands=["admin"])
@dp.throttled(antiflood, rate=1)
async def admin_panel(message: types.Message):
    user = message.from_user
    if user.id in administrators:
        admin_keyboard = get_admin_keyboard()
        await message.answer("Адмін панель", reply_markup=admin_keyboard)
