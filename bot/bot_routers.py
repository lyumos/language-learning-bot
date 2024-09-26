import asyncio
from aiogram import Bot, F, Router
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
from bot.bot_quiz_handler import BotQuizHandler
from bot.bot_db_handler import BotDBHandler

load_dotenv()


class BotRouterHandler:
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

        asyncio.create_task(self.send_daily_reminder())
        asyncio.create_task(self.send_word_of_the_day())

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
            F.text.in_([f"Get stats"]))(self.show_stats)
        self.router.message(Command("start"))(self.choose_initial_mode)
        self.router.message(
            BotTypingHandler.start_mode_choice,
            F.text.in_([self.typing_handler.bot_texts['word_check']])
        )(self.request_word)
        self.router.message(
            BotTypingHandler.check_word_choice
        )(self.check_word_info)
        self.router.message(
            BotTypingHandler.new_word_printing
        )(self.print_word_info)
        self.router.message(
            BotTypingHandler.new_word_handling,
            F.text.in_([f"{emoji.emojize(':left_arrow:')}"])
        )(self.back_to_category_selection)
        self.router.message(
            F.text.in_([f"{emoji.emojize(':thinking_face:')}"])
        )(self.print_extra_info)
        self.router.message(
            BotTypingHandler.new_word_handling,
            F.text.in_([f"{emoji.emojize(':plus:')}"])
        )(self.add_to_collection)
        self.router.message(
            BotTypingHandler.new_word_handling,
            F.text.in_(f"{emoji.emojize(':repeat_button:')}")
        )(self.continue_checking)
        self.router.message(
            F.text.in_([f"{emoji.emojize(':chequered_flag:')}"])
        )(self.start_over)
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
            await self.bot.send_message(user_id,
                                        f"We're returning to the /start because there hasn't been any activity for a while",
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
            # await asyncio.sleep(24 * 60 * 60)

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
            # await asyncio.sleep(24 * 60 * 60)

    async def send_word_of_the_day(self):
        user_ids = self.allowed_user_id
        tasks = [asyncio.create_task(self.send_word_of_the_day_to_user(user_id)) for user_id in user_ids]
        await asyncio.gather(*tasks)

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

    async def show_stats(self, message: Message, state: FSMContext):
        if not await self.user_authorized(message):
            return
        await self.set_inactivity_timer(message.from_user.id, state)
        user_id = str(message.from_user.id)
        words_count = await self.db_handler.get_stats(user_id)
        await self.typing_handler.type_reply(message, f"Here's your progress so far! {emoji.emojize(":party_popper:")}\n\n"
                                                      f"You've added {words_count[0]} new words!\n"
                                                      f"Still working on {words_count[1]} words.\n"
                                                      f"And you’ve mastered {words_count[2]} words already! {emoji.emojize(":flexed_biceps_light_skin_tone:")}\n\n"
                                                      f"Keep it up, and tap /settings or /start when you're ready to continue!")

    async def choose_initial_mode(self, message: Message, state: FSMContext):
        if not await self.user_authorized(message):
            return
        await self.typing_handler.type_answer(message, self.typing_handler.bot_texts['welcome'],
                                              self.typing_handler.keyboards['init'])
        await self.db_handler.add_user_settings(str(message.from_user.id))
        await state.set_state(BotTypingHandler.start_mode_choice)
        await self.set_inactivity_timer(message.from_user.id, state)

    async def request_word(self, message: Message, state: FSMContext):
        if not await self.user_authorized(message):
            return
        await self.set_inactivity_timer(message.from_user.id, state)
        await self.typing_handler.type_reply(message, self.typing_handler.bot_texts['writing_hand'])
        await state.set_state(BotTypingHandler.check_word_choice)

    async def check_word_info(self, message: Message, state: FSMContext):
        if not await self.user_authorized(message):
            return
        await self.set_inactivity_timer(message.from_user.id, state)
        await state.update_data(word=message.text.lower())

        new_word = await self.typing_handler.get_state_info(state, 'word')
        word_info = LanguageProcessing(new_word)

        if word_info.check_definitions() is None:
            if new_word.count(' ') != 0:  #если это выражение из нескольких слов
                await state.update_data(pt_of_speech='Expression')
                await self.typing_handler.type_word_info(message, state, 'Expression', None)
                await state.set_state(BotTypingHandler.new_word_handling)
            else:  #если такого слова не существует
                await self.typing_handler.type_reply(message, self.typing_handler.bot_texts['wrong_word'])
                await state.set_state(BotTypingHandler.check_word_choice)
        else:
            parts_of_speech = word_info.get_word_categories()
            await state.update_data(parts_of_speech=parts_of_speech)
            if len(parts_of_speech) == 1:
                await state.update_data(pt_of_speech=parts_of_speech[0])
                await self.typing_handler.type_word_info(message, state, parts_of_speech[0], True)
                await state.set_state(BotTypingHandler.new_word_handling)
            else:
                await self.typing_handler.type_reply(message, self.typing_handler.bot_texts['word_type'],
                                                     parts_of_speech)
                await state.set_state(BotTypingHandler.new_word_printing)

    async def print_word_info(self, message: Message, state: FSMContext):
        if not await self.user_authorized(message):
            return
        await self.set_inactivity_timer(message.from_user.id, state)
        await state.update_data(pt_of_speech=message.text.lower())
        part_of_speech = await self.typing_handler.get_state_info(state, 'pt_of_speech')
        await self.typing_handler.type_word_info(message, state, part_of_speech, True)
        await state.set_state(BotTypingHandler.new_word_handling)

    async def back_to_category_selection(self, message: Message, state: FSMContext):
        if not await self.user_authorized(message):
            return
        await self.set_inactivity_timer(message.from_user.id, state)
        try:
            parts_of_speech = await self.typing_handler.get_state_info(state, 'parts_of_speech')
            await self.typing_handler.type_reply(message, self.typing_handler.bot_texts['word_type'], parts_of_speech)
            await state.set_state(BotTypingHandler.new_word_printing)
        except KeyError:
            await self.typing_handler.type_word_info(message, state, 'All', None)
            await state.set_state(BotTypingHandler.new_word_handling)

    async def print_extra_info(self, message: Message, state: FSMContext):
        if not await self.user_authorized(message):
            return
        await self.set_inactivity_timer(message.from_user.id, state)
        current_state = await state.get_state()
        if current_state == 'BotTypingHandler:new_word_handling':
            await self.typing_handler.type_extra_info(message, state, 'check')
            await state.set_state(BotTypingHandler.new_word_handling)
        elif current_state == 'BotTypingHandler:learn_words_choice':
            await self.typing_handler.type_extra_info(message, state, 'learn')
            await state.set_state(BotTypingHandler.learn_words_choice)
        elif current_state == 'BotTypingHandler:repeat_words_choice':
            await self.typing_handler.type_extra_info(message, state, 'repeat')
            await state.set_state(BotTypingHandler.repeat_words_choice)

    async def add_to_collection(self, message: Message, state: FSMContext):
        if not await self.user_authorized(message):
            return
        await self.set_inactivity_timer(message.from_user.id, state)
        await self.db_handler.add_word_to_db(message, state)
        await state.set_state(BotTypingHandler.start_mode_choice)

    async def continue_checking(self, message: Message, state: FSMContext):
        if not await self.user_authorized(message):
            return
        await self.set_inactivity_timer(message.from_user.id, state)
        await self.typing_handler.type_reply(message, self.typing_handler.bot_texts['writing_hand'])
        await state.set_state(BotTypingHandler.check_word_choice)

    async def start_over(self, message: Message, state: FSMContext):
        if not await self.user_authorized(message):
            return
        await self.set_inactivity_timer(message.from_user.id, state)
        await self.typing_handler.type_answer(message, self.typing_handler.bot_texts['square_one'],
                                              self.typing_handler.keyboards['init'])
        await state.set_state(BotTypingHandler.start_mode_choice)

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
        if len(words) < 5:
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
        if len(words) < 5:
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
        word_id = await self.quiz_handler.choose_word_for_quiz(state, mode)
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
