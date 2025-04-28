from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram import Router, F

from app.states.register import Register
import app.database.request as rq
import app.keyboards as kb

state_router = Router()


@state_router.message(F.text == 'Регистрация' or Command('register'))
async def register(message: Message, state: FSMContext):
    await state.set_state(Register.first_name)
    await message.answer('Введите ваше имя', reply_markup=ReplyKeyboardRemove())

@state_router.message(Register.first_name)
async def register_name(message: Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await state.set_state(Register.age)
    await message.answer('Укажите ваш возраст в формате числа')

@state_router.message(Register.age)
async def register_age(message: Message, state: FSMContext):
    if int(message.text) < 18:
        await message.answer('Попробуйте зарегистрироваться после наступления вашего совершеннолетия')
        await state.clear()
        return
    elif int(message.text) > 100:
        await message.answer('Пожалуйста, введите свой настоящий возраст')
        return
    else:
        await state.update_data(age=message.text)
        await state.set_state(Register.description)
        await message.answer('Расскажите что-нибудь о себе')

@state_router.message(Register.description)
async def register_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(Register.gender)
    await message.answer('Укажите ваш пол', reply_markup=kb.gender)

@state_router.message(Register.gender)
async def register_gender(message: Message, state: FSMContext):
    if message.text not in ("Женский", "Мужской"):
        await message.answer("Пожалуйста, выберите пол, используя кнопки", reply_markup=kb.gender)
        return

    await state.update_data(gender=message.text)
    await state.set_state(Register.city)
    await message.answer('Укажите ваш город проживания', reply_markup=ReplyKeyboardRemove())

@state_router.message(Register.city)
async def register_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await state.set_state(Register.photo)
    await message.answer('Пожалуйста, загрузите фотографию для вашего профиля')


@state_router.message(Register.photo, F.photo)
async def register_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]
    file_id = photo.file_id

    await state.update_data(photo_path=file_id)

    user_data = await state.get_data()
    tg_id = message.from_user.id
    username = message.from_user.username

    try:
        user_data['age'] = int(user_data['age'])
    except ValueError:
        await message.answer('Неверный формат возраста. Введите число')
        await state.set_state(Register.age)
        return

    success, message_text = await rq.register_user(
        tg_id,
        user_data['first_name'],
        username,
        user_data['age'],
        user_data['description'],
        user_data['gender'],
        user_data['city'],
        user_data['photo_path']
    )

    if success:
        await message.answer(message_text, reply_markup=kb.profile)
    else:
        await message.answer(message_text)
    await state.clear()