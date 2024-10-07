from bot.bot_typing_handler import BotTypingHandler
from db.db import DB
from aiogram import Router, Bot
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import asyncio
import os


class BotRouters(StatesGroup):
    start_mode_choice = State()
    check_word_choice = State()
    repeat_words_choice = State()
    learn_words_choice = State()
    new_word_checking = State()
    new_word_printing = State()
    new_word_handling = State()
    test_start = State()
    check_test = State()
    repeat_start = State()
    check_test_repeat = State()
    settings_choice = State()
    modify_daily_reminder = State()
    modify_word_of_the_day = State()
    modify_quiz_words_count = State()
    modify_quiz_exercises_count = State()

    def __init__(self):
        self.router = Router()
        self.bot_token = os.getenv('BOT_TOKEN')
        self.bot = Bot(token=self.bot_token)
        self.inactivity_timeout = int(os.getenv('INACTIVITY_TIMEOUT'))
        self.allowed_user_id = os.getenv('ALLOWED_USER_ID').split(', ')
        self.user_timers = {}
        self.router = Router()
        self.db = DB()
        self.typing_handler = BotTypingHandler(self.db)
        self._initialize_routers()

    def _initialize_routers(self):
        from bot.bot_routers.word_processing_routers import WordProcessingRouters
        from bot.bot_routers.quiz_routers import QuizRouters
        from bot.bot_routers.settings_routers import SettingsRouters
        from bot.bot_routers.extra_features_routers import ExtraFeaturesRouters
        word_processing_routers = WordProcessingRouters(self)
        quiz_routers = QuizRouters(self.db, self)
        settings_routers = SettingsRouters(self)
        extra_features_routers = ExtraFeaturesRouters(self)

        self.router.include_router(word_processing_routers.router)
        self.router.include_router(quiz_routers.router)
        self.router.include_router(settings_routers.router)
        self.router.include_router(extra_features_routers.router)

    async def user_authorized(self, message: Message):
        if str(message.from_user.id) not in self.allowed_user_id:
            await message.answer("You are not authorized to use this bot.")
            return False
        return True

    async def set_inactivity_timer(self, user_id, state: FSMContext):
        async def handle_inactivity():
            await asyncio.sleep(self.inactivity_timeout)
            await state.set_state(self.start_mode_choice)
            await self.bot.send_message(user_id, self.typing_handler.bot_texts['inactivity_text'],
                                        reply_markup=self.typing_handler.show_keyboard(
                                            self.typing_handler.keyboards['init']))

        if user_id in self.user_timers:
            self.user_timers[user_id].cancel()
        self.user_timers[user_id] = asyncio.create_task(handle_inactivity())