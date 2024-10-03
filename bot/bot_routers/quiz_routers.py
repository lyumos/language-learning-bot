import asyncio
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dotenv import load_dotenv
import emoji
import os

from db.db import DB
from bot.bot_typing_handler import BotTypingHandler
from bot.bot_quiz_handler import BotQuizHandler
from bot.bot_db_handler import BotDBHandler

load_dotenv()


class QuizRouters:
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

        self.quiz_handler = BotQuizHandler(self.typing_handler, self.db_handler, self.db)

        self._setup_routes()

    def _setup_routes(self):
        self.router.message(
            BotTypingHandler.start_mode_choice,
            F.text.in_([f'Learn {emoji.emojize(":nerd_face:")}'])
        )(self.memorize_words)
        self.router.message(
            BotTypingHandler.start_mode_choice,
            F.text.in_(['Repeat'])
        )(self.memorize_words)
        self.router.message(
            BotTypingHandler.learn_words_choice,
            F.text.in_([f"{emoji.emojize(':right_arrow:')}"])
        )(self.move_to_next)
        self.router.message(
            BotTypingHandler.repeat_words_choice,
            F.text.in_([f"{emoji.emojize(':right_arrow:')}"])
        )(self.move_to_next)
        self.router.message(
            BotTypingHandler.test_start,
        )(self.create_quiz)
        self.router.message(
            BotTypingHandler.repeat_start,
        )(self.create_quiz)
        self.router.message(
            BotTypingHandler.check_test,
        )(self.check_chosen_option)
        self.router.message(
            BotTypingHandler.check_test_repeat,
        )(self.check_chosen_option)

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

    async def memorize_words(self, message: Message, state: FSMContext):
        if message.text == 'Repeat':
            words_key = 'words_to_repeat'
            mode = 'repeat'
        else:
            words_key = 'words_to_learn'
            mode = 'learn'
        if not await self.user_authorized(message):
            return
        await self.set_inactivity_timer(message.from_user.id, state)
        try:
            words = await self.typing_handler.get_state_info(state, words_key)
        except KeyError:
            words = []
        if not isinstance(words, list):
            words = []
        user_id = str(message.from_user.id)
        quiz_words_count = self.db.select_setting(user_id, 'quiz_words_count')
        if len(words) < int(quiz_words_count):
            await self.quiz_handler.print_quiz_words(mode, message, state, words, 0)
        else:
            await self.typing_handler.type_reply(message, self.typing_handler.bot_texts['words_ended'],
                                                 self.typing_handler.keyboards['happy_face'])
            await self.db_handler.revert_statuses(state)
            await state.set_state(BotTypingHandler.test_start)

    async def move_to_next(self, message: Message, state: FSMContext):
        current_state = await state.get_state()
        if current_state == 'BotTypingHandler:learn_words_choice':
            words_key = 'words_to_learn'
            mode = 'learn'
            next_state = BotTypingHandler.test_start
        elif current_state == 'BotTypingHandler:repeat_words_choice':
            words_key = 'words_to_repeat'
            mode = 'repeat'
            next_state = BotTypingHandler.repeat_start
        if not await self.user_authorized(message):
            return
        await self.set_inactivity_timer(message.from_user.id, state)
        words = await self.typing_handler.get_state_info(state, words_key)
        user_id = str(message.from_user.id)
        quiz_words_count = self.db.select_setting(user_id, 'quiz_words_count')
        if len(words) < int(quiz_words_count):
            await self.quiz_handler.print_quiz_words(mode, message, state, words, 1)
        else:
            await self.db_handler.revert_statuses(state)
            await self.typing_handler.type_reply(message, self.typing_handler.bot_texts['quiz_time'],
                                                 self.typing_handler.keyboards['happy_face'])
            await state.set_state(next_state)

    async def create_quiz(self, message: Message, state: FSMContext):
        current_state = await state.get_state()
        if current_state == 'BotTypingHandler:test_start':
            mode = 'learn'
            next_state = BotTypingHandler.check_test
        elif current_state == 'BotTypingHandler:repeat_start':
            mode = 'repeat'
            next_state = BotTypingHandler.check_test_repeat
        if not await self.user_authorized(message):
            return
        await self.set_inactivity_timer(message.from_user.id, state)
        user_id = str(message.from_user.id)
        word_id = await self.quiz_handler.choose_word_for_quiz(state, mode, user_id)
        if word_id:
            print_definitions, keyboard = await self.quiz_handler.get_exercise(message, state, word_id)
            await self.typing_handler.type_reply(message, f"{print_definitions}", keyboard)
            await state.set_state(next_state)
        else:
            await self.quiz_handler.print_score(state, message)
            await self.quiz_handler.buffer_clear_out(state, mode)
            await state.set_state(BotTypingHandler.start_mode_choice)

    async def check_chosen_option(self, message: Message, state: FSMContext):
        current_state = await state.get_state()
        if current_state == 'BotTypingHandler:check_test':
            next_state = BotTypingHandler.test_start
        elif current_state == 'BotTypingHandler:check_test_repeat':
            next_state = BotTypingHandler.repeat_start
        chosen_option = message.text.lower()
        right_answer = await self.typing_handler.get_state_info(state, 'right_answer')
        if chosen_option == right_answer:
            await self.typing_handler.type_reply(message, f"Correct! {emoji.emojize(':check_mark_button:')}",
                                                 self.typing_handler.keyboards['next'])
            await self.quiz_handler.increase_score(state)
        else:
            await self.typing_handler.type_reply(message,
                                                 f"Oops, wrong answer! The correct word was <b>{right_answer}</b>",
                                                 self.typing_handler.keyboards['next'])
        await state.set_state(next_state)
