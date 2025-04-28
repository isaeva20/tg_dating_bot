from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.enums.chat_action import ChatAction
from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select

from app.states.views import Views
import app.database.request as rq
import app.keyboards as kb
from app.database.models import async_session
from app.database.models import User

views_router = Router()


def create_profile_text(profile):
  return (
        f"<b>Имя:</b> {profile.get('first_name', 'Не указано')}\n"
        f"<b>Возраст:</b> {profile.get('age', 'Не указано')}\n"
        f"<b>Описание:</b> {profile.get('description', 'Не указано')}\n"
        f"<b>Город:</b> {profile.get('city', 'Не указано')}\n"
    )

@views_router.message(F.text == 'Начать поиск')
async def show_matching_profiles(message: Message, state: FSMContext):
    matching_profiles = await rq.get_matching_profiles(message.from_user.id)

    if matching_profiles is None:
        await message.answer('Произошла ошибка при поиске профилей')
        return

    if not matching_profiles:
        await message.answer('Нет подходящих профилей. Уточните параметры поиска')
        return

    await state.set_state(Views.viewing)
    await state.update_data(profiles=matching_profiles, current_profile_index=0)
    await show_profile(message, state)


async def show_profile(event: Message | CallbackQuery, state: FSMContext):
    data = await state.get_data()
    profiles = data.get('profiles', [])
    current_index = data.get('current_profile_index', 0)

    if not profiles:
        if isinstance(event, Message):
            await event.answer('Нет подходящих профилей')
        elif isinstance(event, CallbackQuery):
            await event.answer('Нет больше профилей')
        return

    if current_index < 0:
        current_index = 0
    elif current_index >= len(profiles):
        current_index = len(profiles) - 1
    await state.update_data(current_profile_index=current_index)
    
    profile = profiles[current_index]
    profile_text = create_profile_text(profile)
    photo_url = profile.get('photo_path')
    
    if isinstance(event, Message):
        if photo_url:
            await event.answer_photo(
                photo=photo_url,
                caption=profile_text,
                parse_mode="HTML",
                reply_markup=kb.marks
            )
        else:
            await event.answer(
                profile_text,
                parse_mode="HTML",
                reply_markup=kb.marks
            )
    elif isinstance(event, CallbackQuery):
        try:
            if photo_url:
                await event.message.edit_media(
                    InputMediaPhoto(
                        media=photo_url,
                        caption=profile_text,
                        parse_mode="HTML"
                    ),
                    reply_markup=kb.marks
                )
            else:
                await event.message.edit_text(
                    profile_text,
                    parse_mode="HTML",
                    reply_markup=kb.marks
                )
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
        await event.answer()

@views_router.callback_query(Views.viewing, F.data.in_({'like', 'dislike'}))
async def navigate_profiles(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    profiles = data.get('profiles', [])
    if not profiles:
        await callback.answer('Нет доступных профилей')
        return

    current_index = data.get('current_profile_index', 0)
    current_profile = profiles[current_index]
    current_profile_id = current_profile['id']
    
    async with async_session() as session:
        async with session.begin():
            try:
                if callback.data == 'like':
                    db_user = await session.scalar(
                        select(User).where(User.tg_id == callback.from_user.id)
                    )
                    await rq.like_user(db_user.id, current_profile_id, session)
                    is_match, user1, user2 = await rq.check_match(db_user.id, current_profile_id, session)
                    
                    if is_match:
                        await send_match_notifications(bot, user1, user2)
                    else:
                        await callback.answer('Вы поставили лайк!')
                
                elif callback.data == 'dislike':
                    profiles = [p for p in profiles if p['id'] != current_profile_id]
                    await state.update_data(profiles=profiles)
            
            except Exception as e:
                await callback.answer(f'Ошибка: {str(e)}')
                return

    await update_profile_index(state, profiles)

async def send_match_notifications(bot: Bot, user1: User, user2: User):
    await bot.send_chat_action(user1.tg_id, ChatAction.TYPING)
    await bot.send_message(
        user1.tg_id,
        f'Взаимный лайк! Пользователь получил уведомление о мэтче.\n'
        f'Вы можете связаться с @{user2.username}'
    )
    await bot.send_chat_action(user2.tg_id, ChatAction.TYPING)
    await bot.send_message(
        user2.tg_id,
        f'Взаимный лайк! Пользователь получил уведомление о мэтче.\n'
        f'Вы можете связаться с @{user1.username}'
    )

async def update_profile_index(state: FSMContext, profiles: list):
    data = await state.get_data()
    current_index = data.get('current_profile_index', 0) + 1
    
    if current_index >= len(profiles):
        if not profiles:
            await state.clear()
            return
        current_index = 0
    
    await state.update_data(current_profile_index=current_index)

