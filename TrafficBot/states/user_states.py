from aiogram.dispatcher.filters.state import StatesGroup, State

class CardState(StatesGroup):
    waiting_for_card = State()