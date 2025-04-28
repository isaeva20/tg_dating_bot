from aiogram.fsm.state import State, StatesGroup

class Update(StatesGroup):
    field = State()
    photo = State()
