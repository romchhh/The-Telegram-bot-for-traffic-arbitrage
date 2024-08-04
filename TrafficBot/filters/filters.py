from aiogram.dispatcher.filters import BoundFilter

from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import types

from aiogram.utils.exceptions import ChatNotFound

from main import bot
from data.config import channel_id, administrators


class IsPrivate(BoundFilter):
    async def check(self, message: types.Message):
        return message.chat.type == types.ChatType.PRIVATE


class IsAdmin(BoundFilter):
    async def check(self, message: types.Message):
        return message.from_user.id in administrators


class IsSubscribed(BoundFilter):
    async def check(self, call: types.CallbackQuery):
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
            return False

        markup.add(InlineKeyboardButton(text='Підписався', callback_data='check'))
        message_text = f"Щоб отримати доступ до функцій бота, <b>потрібно підписатися на канал:</b>"

        if user_status.status == 'left':
            await call.message.edit_text(message_text, reply_markup=markup, disable_web_page_preview=True)
            return False
        else:
            return True
