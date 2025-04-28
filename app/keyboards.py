from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


register = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Регистрация')]], resize_keyboard=True)

gender = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Женский"), KeyboardButton(text="Мужской")]
    ],
    resize_keyboard=True, one_time_keyboard=True
)

profile = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Смотреть профиль')],
    [KeyboardButton(text='Редактировать профиль')],
    [KeyboardButton(text='Удалить профиль')],
    [KeyboardButton(text='Указать параметры поиска')]], resize_keyboard=True)

update_actions = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Имя', callback_data='update_first_name')],
    [InlineKeyboardButton(text='Возраст', callback_data='update_age')],
    [InlineKeyboardButton(text='Описание', callback_data='update_description')],
    [InlineKeyboardButton(text='Пол', callback_data='update_gender')],
    [InlineKeyboardButton(text='Город', callback_data='update_city')],
    [InlineKeyboardButton(text='Фото', callback_data='update_photo_path')]
])

search = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Начать поиск')]], resize_keyboard=True)

views_profiles = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Предыдущий', callback_data='prev_profile')],
    [InlineKeyboardButton(text='Следующий',  callback_data='next_profile')]
])

marks = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Лайк', callback_data='like')],
    [InlineKeyboardButton(text='Дизлайк', callback_data='dislike')]
])