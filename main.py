import os
import asyncio
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timedelta
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.bot_routers.bot_routers_main import BotRouters

os.makedirs('logs', exist_ok=True)


def remove_old_logs(log_dir, days_to_keep=5):
    now = datetime.now()
    for filename in os.listdir(log_dir):
        file_path = os.path.join(log_dir, filename)
        if os.path.isfile(file_path):
            file_creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
            if now - file_creation_time > timedelta(days=days_to_keep):
                os.remove(file_path)
                logging.info(f"Removed old log file: {filename}")


log_handler = TimedRotatingFileHandler(
    "logs/bot.log",
    when="midnight",  # Обновление файла каждый день в полночь
    interval=1,
    encoding='utf-8'
)

log_handler.setLevel(logging.INFO)
log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        log_handler,
        logging.StreamHandler()  # Для вывода логов в консоль
    ]
)



async def periodic_log_cleanup():
    while True:
        remove_old_logs('logs')
        await asyncio.sleep(24 * 60 * 60)  # Запускать каждый день


async def main():
    bot_handler = BotRouters()
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(bot_handler.router)
    await dp.start_polling(bot_handler.bot)


if __name__ == '__main__':
    asyncio.run(main())
