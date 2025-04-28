from aiogram.fsm.state import State, StatesGroup

class Preferences(StatesGroup):
    preferred_gender = State()
    min_age = State()
    max_age = State()
    preferred_city = State()