from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram import Router, F

from app.states.preferences import Preferences
import app.database.request as rq
import app.keyboards as kb

preferences_router = Router()


@preferences_router.message(F.text=='Указать параметры поиска')
async def specify_parametrs(message: Message, state: FSMContext):
    await state.set_state(Preferences.preferred_gender)
    await message.answer('Укажите предпочтительный пол партнера', reply_markup=kb.gender)

@preferences_router.message(Preferences.preferred_gender)
async def specify_gender(message: Message, state: FSMContext):
    if message.text not in ("Женский", "Мужской"):
        await message.answer("Пожалуйста, выберите пол, используя кнопки", reply_markup=kb.gender)
        return
    await state.update_data(preferred_gender=message.text)
    await state.set_state(Preferences.min_age)
    await message.answer('Укажите минимальный возраст партнера в формате числа')

@preferences_router.message(Preferences.min_age)
async def specify_min_age(message: Message, state: FSMContext):
    await state.update_data(min_age=message.text)
    await state.set_state(Preferences.max_age)
    await message.answer('Укажите максимальный возраст партнера в формате числа')

@preferences_router.message(Preferences.max_age)
async def specify_max_age(message: Message, state: FSMContext):
    await state.update_data(max_age=message.text)
    await state.set_state(Preferences.preferred_city)
    await message.answer('Укажите предпочтительный город партнера')

@preferences_router.message(Preferences.preferred_city)
async def specify_city(message: Message, state: FSMContext):
    await state.update_data(preferred_city=message.text)
    preferences_data = await state.get_data()
    tg_id = message.from_user.id
    try:
        preferences_data['min_age'] = int(preferences_data['min_age'])
    except ValueError:
        await message.answer('Неверный формат возраста. Введите число')
        await state.set_state(Preferences.min_age)
        return
    try:
        preferences_data['max_age'] = int(preferences_data['max_age'])
    except ValueError:
        await message.answer('Неверный формат возраста. Введите число')
        await state.set_state(Preferences.max_age)
        return
    success, message_text = await rq.specify_parametrs(
        tg_id,
        preferences_data['preferred_gender'],
        preferences_data['min_age'],
        preferences_data['max_age'],
        preferences_data['preferred_city']
    )

    if success:
        await message.answer(message_text, reply_markup=kb.search)
    else:
        await message.answer(message_text)
    await state.clear()


