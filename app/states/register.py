from aiogram.fsm.state import State, StatesGroup

class Register(StatesGroup):
    first_name = State()
    age = State()
    description = State()
    gender = State()
    city = State()
    photo = State()