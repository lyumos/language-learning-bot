from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dotenv import load_dotenv
import emoji
import os
from aiogram.enums import PollType
from aiogram import types

from bot.bot_typing_handler import BotTypingHandler
from bot.bot_quiz_handler import BotQuizHandler
from bot.bot_db_handler import BotDBHandler
from bot.bot_routers.bot_routers_main import BotRouters
import re
from db.db import DB

load_dotenv()


class QuizRouters:
    def __init__(self, db: DB, bot_routers: BotRouters):
        self.bot_routers = bot_routers
        self.db = db
        self.bot_token = os.getenv('BOT_TOKEN')
        self.bot = Bot(token=self.bot_token)
        self.router = Router()
        self.active_quizzes = {}
        self.typing_handler = BotTypingHandler(self.db)
        self.db_handler = BotDBHandler(self.typing_handler, self.db)
        self.quiz_handler = BotQuizHandler(self.typing_handler, self.db_handler, self.db)
        self._setup_routes()

    def _setup_routes(self):
        self.router.message(
            self.bot_routers.start_mode_choice,
            F.text.in_([f'Learn {emoji.emojize(":nerd_face:")}'])
        )(self.memorize_words)
        self.router.message(
            self.bot_routers.learn_words_choice,
            F.text.in_([f"{emoji.emojize(':right_arrow:')}"])
        )(self.move_to_next)
        self.router.message(
            self.bot_routers.test_start,
        )(self.create_quiz)
        self.router.message(
            self.bot_routers.check_test,
        )(self.check_chosen_option)
        self.router.poll_answer()(self.handle_poll_answer)

    async def memorize_words(self, message: Message, state: FSMContext):
        if message.text == f'Learn {emoji.emojize(":nerd_face:")}':
            words_key = 'words_to_learn'
            mode = 'learn'
        await self.bot_routers.set_inactivity_timer(message.from_user.id, state)
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
            await state.set_state(self.bot_routers.test_start)

    async def move_to_next(self, message: Message, state: FSMContext):
        current_state = await state.get_state()
        if current_state == 'BotRouters:learn_words_choice':
            words_key = 'words_to_learn'
            mode = 'learn'
            next_state = self.bot_routers.test_start
        await self.bot_routers.set_inactivity_timer(message.from_user.id, state)
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
        if current_state == 'BotRouters:test_start':
            mode = 'learn'
            next_state = self.bot_routers.check_test
        await self.bot_routers.set_inactivity_timer(message.from_user.id, state)
        user_id = str(message.from_user.id)
        word_id = await self.quiz_handler.choose_word_for_quiz(state, mode, user_id)
        if word_id:
            print_definitions, keyboard = await self.quiz_handler.get_exercise(message, state, word_id)
            if keyboard:
                if message.text == self.typing_handler.keyboards['happy_face']:
                    await self.typing_handler.type_reply(message, "ok", buttons=self.typing_handler.keyboards['next'])
                right_answer = await self.typing_handler.get_state_info(state, 'right_answer')
                right_answer_index = int(keyboard.index(right_answer))
                question = re.sub(r'</?([bi])>', '', print_definitions)
                poll_message = await self.bot.send_poll(
                    chat_id=message.chat.id,
                    question=question,
                    options=keyboard,
                    type=PollType.QUIZ,
                    correct_option_id=right_answer_index,
                    explanation=f"The correct answer is {right_answer}.",
                    is_anonymous=False
                )
                self.active_quizzes[poll_message.poll.id] = right_answer_index
            else:
                await self.typing_handler.type_reply(message, f"{print_definitions}", keyboard)
                await state.set_state(next_state)
        else:
            await self.quiz_handler.print_score(state, message)
            await self.quiz_handler.buffer_clear_out(state, mode)
            await state.set_state(self.bot_routers.start_mode_choice)

    async def check_chosen_option(self, message: Message, state: FSMContext):
        current_state = await state.get_state()
        if current_state == 'BotRouters:check_test':
            next_state = self.bot_routers.test_start
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

    async def handle_poll_answer(self, poll_answer: types.PollAnswer, state: FSMContext):
        poll_id = poll_answer.poll_id
        chosen_option = poll_answer.option_ids[0]

        if poll_id in self.active_quizzes:
            correct_option_id = self.active_quizzes[poll_id]

            if chosen_option == correct_option_id:
                await self.quiz_handler.increase_score(state)
