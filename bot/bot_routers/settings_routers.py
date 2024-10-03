import asyncio
from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dotenv import load_dotenv
import os

from db.db import DB
from bot.bot_typing_handler import BotTypingHandler
from bot.bot_db_handler import BotDBHandler

load_dotenv()


class SettingsRouters:
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

    def _setup_routes(self):
        self.router.message(Command("settings"))(self.get_settings)
        self.router.message(
            BotTypingHandler.settings_choice,
            F.text.in_([f"Daily reminder"]))(self.modify_daily_reminder)
        self.router.message(
            BotTypingHandler.modify_daily_reminder,
            F.text.in_([f"Enable"]))(self.enable_daily_reminder)
        self.router.message(
            BotTypingHandler.modify_daily_reminder,
            F.text.in_([f"Disable"]))(self.disable_daily_reminder)
        self.router.message(
            BotTypingHandler.settings_choice,
            F.text.in_([f"Word of the day"]))(self.modify_word_of_the_day)
        self.router.message(
            BotTypingHandler.modify_word_of_the_day,
            F.text.in_([f"Enable"]))(self.enable_word_of_the_day)
        self.router.message(
            BotTypingHandler.modify_word_of_the_day,
            F.text.in_([f"Disable"]))(self.disable_word_of_the_day)
        self.router.message(
            BotTypingHandler.settings_choice,
            F.text.in_([f"Quiz words"]))(self.modify_quiz_words_count)
        self.router.message(
            BotTypingHandler.modify_quiz_words_count
        )(self.set_quiz_words_count)
        self.router.message(
            BotTypingHandler.settings_choice,
            F.text.in_([f"Number of exercises"]))(self.modify_quiz_exercises_count)
        self.router.message(
            BotTypingHandler.modify_quiz_exercises_count
        )(self.set_quiz_exercises_count)

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

    async def get_settings(self, message: Message, state: FSMContext):
        if not await self.user_authorized(message):
            return
        await self.set_inactivity_timer(message.from_user.id, state)
        await self.typing_handler.type_answer(message, self.typing_handler.bot_texts['settings'],
                                              self.typing_handler.keyboards['settings'])
        await state.set_state(BotTypingHandler.settings_choice)

    async def modify_daily_reminder(self, message: Message, state: FSMContext):
        if not await self.user_authorized(message):
            return
        await self.set_inactivity_timer(message.from_user.id, state)
        await self.typing_handler.type_reply(message, self.typing_handler.bot_texts['modify_settings'],
                                             self.typing_handler.keyboards['enable/disable'])
        await state.set_state(BotTypingHandler.modify_daily_reminder)

    async def enable_daily_reminder(self, message: Message):
        user_id = str(message.from_user.id)
        await self.db_handler.modify_settings(user_id, 'daily_reminder', 'enabled')
        await self.typing_handler.type_reply(message, "Daily reminder enabled! Tap /settings or /start to continue")

    async def disable_daily_reminder(self, message: Message):
        user_id = str(message.from_user.id)
        await self.db_handler.modify_settings(user_id, 'daily_reminder', 'disabled')
        await self.typing_handler.type_reply(message, "Daily reminder disabled! Tap /settings or /start to continue")

    async def modify_word_of_the_day(self, message: Message, state: FSMContext):
        if not await self.user_authorized(message):
            return
        await self.set_inactivity_timer(message.from_user.id, state)
        await self.typing_handler.type_reply(message, self.typing_handler.bot_texts['modify_settings'],
                                             self.typing_handler.keyboards['enable/disable'])
        await state.set_state(BotTypingHandler.modify_word_of_the_day)

    async def enable_word_of_the_day(self, message: Message):
        user_id = str(message.from_user.id)
        await self.db_handler.modify_settings(user_id, 'word_of_the_day', 'enabled')
        await self.typing_handler.type_reply(message, "Word of the day enabled! Tap /settings or /start to continue")

    async def disable_word_of_the_day(self, message: Message):
        user_id = str(message.from_user.id)
        await self.db_handler.modify_settings(user_id, 'word_of_the_day', 'disabled')
        await self.typing_handler.type_reply(message, "Word of the day disabled! Tap /settings or /start to continue")

    async def modify_quiz_words_count(self, message: Message, state: FSMContext):
        if not await self.user_authorized(message):
            return
        await self.set_inactivity_timer(message.from_user.id, state)
        await self.typing_handler.type_reply(message, self.typing_handler.bot_texts['set_quiz_words_count'])
        await state.set_state(BotTypingHandler.modify_quiz_words_count)

    async def set_quiz_words_count(self, message: Message, state: FSMContext):
        if not await self.user_authorized(message):
            return
        await self.set_inactivity_timer(message.from_user.id, state)
        user_id = str(message.from_user.id)
        words_count = int(message.text)
        await self.db_handler.modify_settings(user_id, 'quiz_words_count', words_count)
        await self.typing_handler.type_reply(message, "The new amount is set! Tap /settings or /start to continue")
        await state.set_state(BotTypingHandler.start_mode_choice)

    async def modify_quiz_exercises_count(self, message: Message, state: FSMContext):
        if not await self.user_authorized(message):
            return
        await self.set_inactivity_timer(message.from_user.id, state)
        await self.typing_handler.type_reply(message, self.typing_handler.bot_texts['set_quiz_exercises_count'])
        await state.set_state(BotTypingHandler.modify_quiz_exercises_count)

    async def set_quiz_exercises_count(self, message: Message, state: FSMContext):
        if not await self.user_authorized(message):
            return
        await self.set_inactivity_timer(message.from_user.id, state)
        user_id = str(message.from_user.id)
        exercises_count = int(message.text)
        await self.db_handler.modify_settings(user_id, 'quiz_exercises_count', exercises_count)
        await self.typing_handler.type_reply(message, "The new amount is set! Tap /settings or /start to continue")
        await state.set_state(BotTypingHandler.start_mode_choice)