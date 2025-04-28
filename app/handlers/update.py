from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram import Router, F, Bot

from app.states.update import Update
import app.database.request as rq
import app.keyboards as kb

update_router = Router()


@update_router.callback_query(F.data.startswith('update_'))
async def update_field_callback(callback_query: CallbackQuery, state: FSMContext, bot: Bot):
    field_name = callback_query.data.replace("update_", "")
    await callback_query.answer()
    if field_name == 'photo_path':
        await state.set_state(Update.photo)
        await bot.send_message(callback_query.from_user.id, 'Отправьте новое фото')
    elif field_name == 'gender':
        await bot.send_message(callback_query.from_user.id, 'Укажите ваш пол', reply_markup=kb.gender)
        await state.set_state(Update.field)
        await state.update_data(field_name=field_name)
    else:
        await state.set_state(Update.field)
        await state.update_data(field_name=field_name)
        await bot.send_message(callback_query.from_user.id, f"Укажите значение для выбранного поля:")

    await callback_query.answer()

@update_router.message(Update.field)
async def update_field_handler(message: Message, state: FSMContext):
    user_data = await state.get_data()
    field_name = user_data["field_name"]
    if field_name == 'age':
        try:
            new_value = int(message.text)
            if int(new_value) < 18:
                await message.answer('Попробуйте зарегистрироваться после наступления вашего совершеннолетия')
                await state.clear()
                return
            elif int(new_value) > 100:
                await message.answer('Пожалуйста, введите свой настоящий возраст')
                return
        except ValueError:
            await message.answer('Укажите возраст в числовом формате')
            return
    else:
        new_value = message.text

    success, message_text = await rq.update_user_profile(message.from_user.id, field_name, new_value)
    if success:
        await message.answer(message_text, reply_markup=kb.profile)
    else:
        await message.answer(message_text, reply_markup=kb.profile)

    await state.clear()

@update_router.message(Update.photo, F.photo)
async def update_photo_handler(message: Message, state: FSMContext):
    photo = message.photo[-1]
    file_id = photo.file_id
    await state.update_data(photo_path=file_id)

    user_data = await state.get_data()
    success, message_text = await rq.update_user_profile(message.from_user.id, 'photo_path', user_data['photo_path'])
    if success:
        await message.answer(message_text, reply_markup=kb.profile)
    else:
        await message.answer(message_text, reply_markup=kb.profile)
    await state.clear()