from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dotenv import load_dotenv
import emoji
import os

from dictionary.my_dictionary_collaboration import LanguageProcessing
from bot.bot_typing_handler import BotTypingHandler
from bot.bot_db_handler import BotDBHandler
from bot.bot_routers.bot_routers_main import BotRouters

load_dotenv()


class WordProcessingRouters:
    def __init__(self, bot_routers: BotRouters):
        self.bot_routers = bot_routers
        self.bot_token = os.getenv('BOT_TOKEN')
        self.bot = Bot(token=self.bot_token)
        self.router = Router()
        self.user_timers = {}
        self.typing_handler = BotTypingHandler(self.bot_routers.db)
        self.db_handler = BotDBHandler(self.typing_handler, self.bot_routers.db)
        self._setup_routes()

    def _setup_routes(self):
        self.router.message(Command("start"))(self.choose_initial_mode)
        self.router.message(
            self.bot_routers.start_mode_choice,
            F.text.in_([self.typing_handler.bot_texts['word_check']])
        )(self.request_word)
        self.router.message(
            self.bot_routers.check_word_choice
        )(self.check_word_info)
        self.router.message(
            self.bot_routers.new_word_printing
        )(self.print_word_info)
        self.router.message(
            self.bot_routers.new_word_handling,
            F.text.in_([f"{emoji.emojize(':left_arrow:')}"])
        )(self.back_to_category_selection)
        self.router.message(
            F.text.in_([f"{emoji.emojize(':thinking_face:')}"])
        )(self.print_extra_info)
        self.router.message(
            self.bot_routers.new_word_handling,
            F.text.in_([f"{emoji.emojize(':plus:')}"])
        )(self.add_to_collection)
        self.router.message(
            self.bot_routers.new_word_handling,
            F.text.in_(f"{emoji.emojize(':repeat_button:')}")
        )(self.continue_checking)
        self.router.message(
            F.text.in_([f"{emoji.emojize(':chequered_flag:')}"])
        )(self.start_over)

    async def choose_initial_mode(self, message: Message, state: FSMContext):
        if not await self.bot_routers.user_authorized(message):
            return
        await self.typing_handler.type_answer(message, self.typing_handler.bot_texts['welcome'],
                                              self.typing_handler.keyboards['init'])
        await self.db_handler.check_lost_words()
        await self.db_handler.add_user_settings(str(message.from_user.id))
        await state.set_state(self.bot_routers.start_mode_choice)
        await self.bot_routers.set_inactivity_timer(message.from_user.id, state)

    async def request_word(self, message: Message, state: FSMContext):
        await self.bot_routers.set_inactivity_timer(message.from_user.id, state)
        await self.typing_handler.type_reply(message, self.typing_handler.bot_texts['writing_hand'])
        await state.set_state(self.bot_routers.check_word_choice)

    async def check_word_info(self, message: Message, state: FSMContext):
        await self.bot_routers.set_inactivity_timer(message.from_user.id, state)
        await state.update_data(word=message.text.lower())

        new_word = await self.typing_handler.get_state_info(state, 'word')
        word_info = LanguageProcessing(new_word)

        if word_info.check_definitions() is None:
            if new_word.count(' ') != 0:  # если это выражение из нескольких слов
                await state.update_data(pt_of_speech='Expression')
                await self.typing_handler.type_word_info(message, state, 'Expression', None)
                await state.set_state(self.bot_routers.new_word_handling)
            else:  # если такого слова не существует
                await self.typing_handler.type_reply(message, self.typing_handler.bot_texts['wrong_word'])
                await state.set_state(self.bot_routers.check_word_choice)
        else:
            parts_of_speech = word_info.get_word_categories()
            await state.update_data(parts_of_speech=parts_of_speech)
            if len(parts_of_speech) == 1:
                await state.update_data(pt_of_speech=parts_of_speech[0])
                await self.typing_handler.type_word_info(message, state, parts_of_speech[0], True)
                await state.set_state(self.bot_routers.new_word_handling)
            else:
                await self.typing_handler.type_reply(message, self.typing_handler.bot_texts['word_type'],
                                                     parts_of_speech)
                await state.set_state(self.bot_routers.new_word_printing)

    async def print_word_info(self, message: Message, state: FSMContext):
        await self.bot_routers.set_inactivity_timer(message.from_user.id, state)
        await state.update_data(pt_of_speech=message.text.lower())
        part_of_speech = await self.typing_handler.get_state_info(state, 'pt_of_speech')
        await self.typing_handler.type_word_info(message, state, part_of_speech, True)
        await state.set_state(self.bot_routers.new_word_handling)

    async def back_to_category_selection(self, message: Message, state: FSMContext):
        await self.bot_routers.set_inactivity_timer(message.from_user.id, state)
        try:
            parts_of_speech = await self.typing_handler.get_state_info(state, 'parts_of_speech')
            await self.typing_handler.type_reply(message, self.typing_handler.bot_texts['word_type'], parts_of_speech)
            await state.set_state(self.bot_routers.new_word_printing)
        except KeyError:
            await self.typing_handler.type_word_info(message, state, 'All', None)
            await state.set_state(self.bot_routers.new_word_handling)

    async def print_extra_info(self, message: Message, state: FSMContext):
        await self.bot_routers.set_inactivity_timer(message.from_user.id, state)
        current_state = await state.get_state()
        if current_state == 'BotTypingHandler:new_word_handling':
            await self.typing_handler.type_extra_info(message, state, 'check')
            await state.set_state(self.bot_routers.new_word_handling)
        elif current_state == 'BotTypingHandler:learn_words_choice':
            await self.typing_handler.type_extra_info(message, state, 'learn')
            await state.set_state(self.bot_routers.learn_words_choice)
        elif current_state == 'BotTypingHandler:repeat_words_choice':
            await self.typing_handler.type_extra_info(message, state, 'repeat')
            await state.set_state(self.bot_routers.repeat_words_choice)

    async def add_to_collection(self, message: Message, state: FSMContext):
        await self.bot_routers.set_inactivity_timer(message.from_user.id, state)
        await self.db_handler.add_word_to_db(message, state)
        await state.set_state(self.bot_routers.start_mode_choice)

    async def continue_checking(self, message: Message, state: FSMContext):
        await self.bot_routers.set_inactivity_timer(message.from_user.id, state)
        await self.typing_handler.type_reply(message, self.typing_handler.bot_texts['writing_hand'])
        await state.set_state(self.bot_routers.check_word_choice)

    async def start_over(self, message: Message, state: FSMContext):
        await self.bot_routers.set_inactivity_timer(message.from_user.id, state)
        await self.typing_handler.type_answer(message, self.typing_handler.bot_texts['square_one'],
                                              self.typing_handler.keyboards['init'])
        await state.set_state(self.bot_routers.start_mode_choice)
