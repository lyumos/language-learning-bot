from bot.bot_routers import BotRouterHandler
import asyncio
import os
import logging
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/bot.log", mode='a', encoding='utf-8'),  # Логи пишутся в файл
        logging.StreamHandler()  # Логи выводятся в консоль
    ]
)


async def main():
    bot_handler = BotRouterHandler()

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(bot_handler.router)
    await dp.start_polling(bot_handler.bot)


if __name__ == '__main__':
    asyncio.run(main())
