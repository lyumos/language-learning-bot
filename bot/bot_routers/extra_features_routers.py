import asyncio
from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
from aiogram.types import Message
from dotenv import load_dotenv
from aiogram.enums import ParseMode
import emoji
import os

from db.db import DB
from dictionary.my_dictionary_collaboration import LanguageProcessing
from bot.bot_typing_handler import BotTypingHandler
from bot.bot_db_handler import BotDBHandler

load_dotenv()


class ExtraFeaturesRouters:
    def __init__(self):
        self.bot_token = os.getenv('BOT_TOKEN')
        self.inactivity_timeout = int(os.getenv('INACTIVITY_TIMEOUT'))
        self.allowed_user_id = os.getenv('ALLOWED_USER_ID').split(', ')

        self.bot = Bot(token=self.bot_token)
        self.router = Router()
        self.user_timers = {}

        self.db = DB()
        self.typing_handler = BotTypingHandler(self.db)
        self.db_handler = BotDBHandler(self.typing_handler, self.db)

        self._setup_routes()

        asyncio.create_task(self.send_daily_reminder())
        asyncio.create_task(self.send_word_of_the_day())

    def _setup_routes(self):
        self.router.message(Command("help"))(self.get_help)
        self.router.message(Command("stats"))(self.show_stats)

    async def user_authorized(self, message):
        if str(message.from_user.id) not in self.allowed_user_id:
            await message.answer("You are not authorized to use this bot.")
            return False
        return True

    async def set_inactivity_timer(self, user_id, state: FSMContext):
        async def handle_inactivity():
            await asyncio.sleep(self.inactivity_timeout)
            await state.set_state(BotTypingHandler.start_mode_choice)
            await self.bot.send_message(user_id, self.typing_handler.bot_texts['inactivity_text'],
                                        reply_markup=self.typing_handler.show_keyboard(
                                            self.typing_handler.keyboards['init']))

        if user_id in self.user_timers:
            self.user_timers[user_id].cancel()
        self.user_timers[user_id] = asyncio.create_task(handle_inactivity())

    async def send_reminder_to_user(self, user_id):
        while True:
            now = datetime.now()
            target_time = now.replace(hour=17, minute=0, second=0, microsecond=0)
            if now > target_time:
                target_time += timedelta(days=1)
            wait_time = (target_time - now).total_seconds()
            await asyncio.sleep(wait_time)
            message_needed = self.db.select_date_delta(user_id)
            reminder_enabled = self.db.select_setting(user_id, 'daily_reminder')
            if message_needed and reminder_enabled:
                await self.bot.send_message(user_id, self.typing_handler.bot_texts['daily_reminder'])

    async def send_daily_reminder(self):
        user_ids = self.allowed_user_id
        tasks = [asyncio.create_task(self.send_reminder_to_user(user_id)) for user_id in user_ids]
        await asyncio.gather(*tasks)

    async def send_word_of_the_day_to_user(self, user_id):
        while True:
            now = datetime.now()
            target_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
            if now > target_time:
                target_time += timedelta(days=1)
            wait_time = (target_time - now).total_seconds()
            await asyncio.sleep(wait_time)
            notification_enabled = self.db.select_setting(user_id, 'word_of_the_day')
            if notification_enabled:
                word_info = self.db.select_word_of_the_day(user_id)
                if word_info:
                    word = word_info[0]
                    category = word_info[1]
                    word_handling = LanguageProcessing(word)
                    if category == 'Expression':
                        translation = word_handling.get_word_translations(category)
                        print_definitions = self.typing_handler.prepare_sentences_for_print(None, category, translation)
                    else:
                        definitions = word_handling.get_word_definitions(category)
                        translation = word_handling.get_word_translations(category)
                        print_definitions = self.typing_handler.prepare_sentences_for_print(definitions, category,
                                                                                            translation)
                    await self.bot.send_message(
                        user_id,
                        f"Today's word of the day is <b>{word}</b>!\n\n{print_definitions}",
                        parse_mode=ParseMode.HTML
                    )

    async def send_word_of_the_day(self):
        user_ids = self.allowed_user_id
        tasks = [asyncio.create_task(self.send_word_of_the_day_to_user(user_id)) for user_id in user_ids]
        await asyncio.gather(*tasks)

    async def get_help(self, message: Message, state: FSMContext):
        if not await self.user_authorized(message):
            return
        await self.set_inactivity_timer(message.from_user.id, state)
        await self.typing_handler.type_reply(message, self.typing_handler.bot_texts['help_text'])

    async def show_stats(self, message: Message, state: FSMContext):
        if not await self.user_authorized(message):
            return
        await self.set_inactivity_timer(message.from_user.id, state)
        user_id = str(message.from_user.id)
        words_count = await self.db_handler.get_stats(user_id)
        await self.typing_handler.type_reply(message,
                                             f"Here's your progress so far! {emoji.emojize(":party_popper:")}\n\n"
                                             f"You've added {words_count[0]} new words!\n"
                                             f"Still working on {words_count[1]} words.\n"
                                             f"And you’ve mastered {words_count[2]} words already! {emoji.emojize(":flexed_biceps_light_skin_tone:")}\n\n"
                                             f"Keep it up, /start when you're ready to continue!")
