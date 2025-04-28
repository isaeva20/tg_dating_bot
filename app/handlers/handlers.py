from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import CommandStart, Command
import app.database.request as rq
import app.keyboards as kb

handler_router = Router()

@handler_router.message(CommandStart())
async def cmd_start(message: Message):
    await rq.set_user(message.from_user.id, message.from_user.username)
    await message.answer('Привет! Чтобы пользоваться всеми функциями бота, пройдите регистрацию', reply_markup=kb.register)

@handler_router.message(F.text == 'Смотреть профиль')
async def show_profile(message: Message):
    user, photo_url = await rq.get_user_profile(message.from_user.id)
    if user:
        profile_text = (
            f"<b>Имя:</b> {user.first_name}\n"
            f"<b>Возраст:</b> {user.age}\n"
            f"<b>Описание:</b> {user.description}\n"
            f"<b>Город:</b> {user.city}\n"
        )
        if photo_url:
            try:
                await message.answer_photo(photo_url, caption=profile_text, parse_mode="HTML", reply_markup=kb.profile)
            except Exception as e:
                print(f"Ошибка при отправке фото: {e}")
                profile_text += f"<i>(Ошибка при отправке фото)</i>\n"
                await message.answer(profile_text, parse_mode="HTML", reply_markup=ReplyKeyboardRemove())

        else:
            await message.answer(profile_text, parse_mode="HTML", reply_markup=kb.profile)
    else:
        await message.answer('Пользователь не найден или не зарегистрирован')

@handler_router.message(F.text == 'Редактировать профиль')
async def update_profile_command(message: Message):
    await message.answer('Выберите поле для редактирования:', reply_markup=kb.update_actions)

@handler_router.message(F.text == 'Удалить профиль') 
async def delete_profile_command(message: Message):
    tg_id = message.from_user.id
    success, message_text = await rq.delete_user_profile(tg_id)

    if success:
        await message.answer(message_text)
    else:
        await message.answer(message_text)

