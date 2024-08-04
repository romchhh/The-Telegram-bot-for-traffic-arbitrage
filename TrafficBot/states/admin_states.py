from aiogram.dispatcher.filters.state import State, StatesGroup

class AddChannel(StatesGroup):
    waiting_for_name = State()
    waiting_for_link = State()
    waiting_for_id = State()
    waiting_for_category = State()
    waiting_for_payment = State()
    waiting_for_order = State()
    waiting_for_payment_type = State()
    waiting_for_commentary = State()
    confirm = State()
    
    
class BroadcastState(StatesGroup):
    text = State()
    photo = State()
    preview = State()

class AddOfferState(StatesGroup):
    waiting_for_quantity = State()