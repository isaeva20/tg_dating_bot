import asyncio
from aiogram import Bot, Dispatcher, F
from app.handlers.handlers import handler_router
from app.handlers.register import state_router
from app.handlers.update import update_router
from app.handlers.preferences import preferences_router
from app.handlers.views import views_router
from config import TOKEN
from app.database.models import async_main

async def main():
    await async_main()
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(handler_router)
    dp.include_router(state_router)
    dp.include_router(update_router)
    dp.include_router(preferences_router)
    dp.include_router(views_router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('cancel')