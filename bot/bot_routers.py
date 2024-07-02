import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from db.db import BotDB
from dictionary.my_dictionary_collaboration import LanguageProcessing
import emoji
from bot.bot_typing_handler import BotTypingHandler
from dotenv import load_dotenv
import os
from bot_quiz_handler import show_pick_contest, buffer_clear_out, increase_score, print_score, choose_word_for_quiz

load_dotenv()
bot_token = os.getenv('BOT_TOKEN')
bot = Bot(token=bot_token)
logging.basicConfig(level=logging.INFO)
bot_handler = BotTypingHandler()
router = Router()
db = BotDB(os.getenv('DB_NAME'))
INACTIVITY_TIMEOUT = 300
user_timers = {}
allowed_user_id = os.getenv('ALLOWED_USER_ID').split(', ')


async def set_inactivity_timer(user_id, state: FSMContext):
    async def handle_inactivity():
        await asyncio.sleep(INACTIVITY_TIMEOUT)
        await state.set_state(BotTypingHandler.start_mode_choice)
        await bot.send_message(user_id,
                               f"We're returning to the /start because there hasn't been any activity for a while",
                               reply_markup=bot_handler.show_keyboard(bot_handler.keyboards['init']))

    if user_id in user_timers:
        user_timers[user_id].cancel()
    user_timers[user_id] = asyncio.create_task(handle_inactivity())


async def user_authorized(message):
    if str(message.from_user.id) not in allowed_user_id:
        await message.answer("You are not authorized to use this bot.")
        return False
    return True


@router.message(Command("start"))
async def choose_initial_mode(message: Message, state: FSMContext):
    if not await user_authorized(message):
        return
    await bot_handler.type_answer(message, bot_handler.bot_texts['welcome'], bot_handler.keyboards['init'])
    await state.set_state(BotTypingHandler.start_mode_choice)
    await set_inactivity_timer(message.from_user.id, state)


@router.message(
    BotTypingHandler.start_mode_choice,
    F.text.in_([bot_handler.bot_texts['word_check']])
)
async def request_word(message: Message, state: FSMContext):
    if not await user_authorized(message):
        return
    await set_inactivity_timer(message.from_user.id, state)
    await bot_handler.type_reply(message, bot_handler.bot_texts['writing_hand'])
    await state.set_state(BotTypingHandler.check_word_choice)


@router.message(
    BotTypingHandler.check_word_choice
)
async def check_word_info(message: Message, state: FSMContext):
    if not await user_authorized(message):
        return
    await set_inactivity_timer(message.from_user.id, state)
    await state.update_data(word=message.text.lower())

    new_word = await bot_handler.get_state_info(state, 'word')
    word_info = LanguageProcessing(new_word)

    if word_info.check_definitions() is None:
        if new_word.count(' ') != 0:
            await state.update_data(pt_of_speech='All')
            await bot_handler.type_word_info(message, state, 'All', None)
            await state.set_state(BotTypingHandler.new_word_handling)
        else:
            await bot_handler.type_reply(message, bot_handler.bot_texts['wrong_word'])
            await state.set_state(BotTypingHandler.check_word_choice)
    else:
        parts_of_speech = word_info.get_word_categories()
        await state.update_data(parts_of_speech=parts_of_speech)
        if len(parts_of_speech) == 1:
            await state.update_data(pt_of_speech=parts_of_speech[0])
            await bot_handler.type_word_info(message, state, parts_of_speech[0], True)
            await state.set_state(BotTypingHandler.new_word_handling)
        else:
            await bot_handler.type_reply(message, bot_handler.bot_texts['word_type'], parts_of_speech)
            await state.set_state(BotTypingHandler.new_word_printing)


@router.message(
    BotTypingHandler.new_word_printing
)
async def print_word_info(message: Message, state: FSMContext):
    if not await user_authorized(message):
        return
    await set_inactivity_timer(message.from_user.id, state)
    await state.update_data(pt_of_speech=message.text.lower())
    part_of_speech = await bot_handler.get_state_info(state, 'pt_of_speech')
    await bot_handler.type_word_info(message, state, part_of_speech, True)
    await state.set_state(BotTypingHandler.new_word_handling)


@router.message(
    BotTypingHandler.new_word_handling,
    F.text.in_([f"{emoji.emojize(":left_arrow:")}"])
)
async def back_to_category_selection(message: Message, state: FSMContext):
    if not await user_authorized(message):
        return
    await set_inactivity_timer(message.from_user.id, state)
    try:
        parts_of_speech = await bot_handler.get_state_info(state, 'parts_of_speech')
        await bot_handler.type_reply(message, bot_handler.bot_texts['word_type'], parts_of_speech)
        await state.set_state(BotTypingHandler.new_word_printing)
    except KeyError:
        await bot_handler.type_word_info(message, state, 'All', None)
        await state.set_state(BotTypingHandler.new_word_handling)


@router.message(
    F.text.in_([f"{emoji.emojize(":thinking_face:")}"])
)
async def print_extra_info(message: Message, state: FSMContext):
    if not await user_authorized(message):
        return
    await set_inactivity_timer(message.from_user.id, state)
    current_state = await state.get_state()
    if current_state == 'BotTypingHandler:new_word_handling':
        await bot_handler.type_extra_info(message, state)
        await state.set_state(BotTypingHandler.new_word_handling)
    elif current_state == 'BotTypingHandler:learn_words_choice':
        await bot_handler.type_extra_info(message, state, db)
        await state.set_state(BotTypingHandler.learn_words_choice)
    elif current_state == 'BotTypingHandler:repeat_words_choice':
        await bot_handler.type_extra_info(message, state, db)
        await state.set_state(BotTypingHandler.repeat_words_choice)


@router.message(
    BotTypingHandler.new_word_handling,
    F.text.in_([f"{emoji.emojize(":plus:")}"])
)
async def add_to_collection(message: Message, state: FSMContext):
    if not await user_authorized(message):
        return
    await set_inactivity_timer(message.from_user.id, state)
    await bot_handler.add_word_to_db(message, state, db)
    await state.set_state(BotTypingHandler.start_mode_choice)


@router.message(
    BotTypingHandler.new_word_handling,
    F.text.in_(f"{emoji.emojize(":repeat_button:")}")
)
async def continue_checking(message: Message, state: FSMContext):
    if not await user_authorized(message):
        return
    await set_inactivity_timer(message.from_user.id, state)
    await bot_handler.type_reply(message, bot_handler.bot_texts['writing_hand'])
    await state.set_state(BotTypingHandler.check_word_choice)


@router.message(
    F.text.in_([f"{emoji.emojize(":chequered_flag:")}"])
)
async def start_over(message: Message, state: FSMContext):
    if not await user_authorized(message):
        return
    await set_inactivity_timer(message.from_user.id, state)
    await bot_handler.type_answer(message, bot_handler.bot_texts['square_one'], bot_handler.keyboards['init'])
    await state.set_state(BotTypingHandler.start_mode_choice)


@router.message(
    BotTypingHandler.start_mode_choice,
    F.text.in_([f'Learn {emoji.emojize(":nerd_face:")}'])
)
@router.message(
    BotTypingHandler.start_mode_choice,
    F.text.in_(['Repeat'])
)
async def memorize_words(message: Message, state: FSMContext):
    if message.text == 'Repeat':
        words_key = 'words_to_repeat'
        mode = 'repeat'
    else:
        words_key = 'words_to_learn'
        mode = 'learn'
    if not await user_authorized(message):
        return
    await set_inactivity_timer(message.from_user.id, state)
    try:
        words = await bot_handler.get_state_info(state, words_key)
    except KeyError:
        words = []
    if not isinstance(words, list):
        words = []
    if len(words) < 5:
        await bot_handler.print_quiz_words(mode, message, state, words, db, 0)
    else:
        await bot_handler.type_reply(message, bot_handler.bot_texts['words_ended'], bot_handler.keyboards['happy_face'])
        await bot_handler.revert_statuses(state, db)
        await state.set_state(BotTypingHandler.test_start)


@router.message(
    BotTypingHandler.learn_words_choice,
    F.text.in_([f"{emoji.emojize(':right_arrow:')}"])
)
@router.message(
    BotTypingHandler.repeat_words_choice,
    F.text.in_([f"{emoji.emojize(':right_arrow:')}"])
)
async def move_to_next(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == 'BotTypingHandler:learn_words_choice':
        words_key = 'words_to_learn'
        mode = 'learn'
        next_state = BotTypingHandler.test_start
    elif current_state == 'BotTypingHandler:repeat_words_choice':
        words_key = 'words_to_repeat'
        mode = 'repeat'
        next_state = BotTypingHandler.repeat_start
    if not await user_authorized(message):
        return
    await set_inactivity_timer(message.from_user.id, state)
    words = await bot_handler.get_state_info(state, words_key)
    if len(words) < 5:
        await bot_handler.print_quiz_words(mode, message, state, words, db, 1)
    else:
        await bot_handler.revert_statuses(state, db)
        await bot_handler.type_reply(message, bot_handler.bot_texts['quiz_time'], bot_handler.keyboards['happy_face'])
        await state.set_state(next_state)


@router.message(
    BotTypingHandler.test_start,
)
@router.message(
    BotTypingHandler.repeat_start,
)
async def create_quiz(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == 'BotTypingHandler:test_start':
        mode = 'learn'
        next_state = BotTypingHandler.check_test
    elif current_state == 'BotTypingHandler:repeat_start':
        mode = 'repeat'
        next_state = BotTypingHandler.check_test_repeat
    if not await user_authorized(message):
        return
    await set_inactivity_timer(message.from_user.id, state)
    word_id = await choose_word_for_quiz(state, mode)
    if word_id:
        print_definitions, keyboard = await show_pick_contest(state, word_id, db)
        await bot_handler.type_reply(message, f"{print_definitions}", keyboard)
        await state.set_state(next_state)
    else:
        await print_score(state, message)
        await buffer_clear_out(state, mode)
        await state.set_state(BotTypingHandler.start_mode_choice)


@router.message(
    BotTypingHandler.check_test,
)
@router.message(
    BotTypingHandler.check_test_repeat,
)
async def check_chosen_option(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == 'BotTypingHandler:check_test':
        next_state = BotTypingHandler.test_start
    elif current_state == 'BotTypingHandler:check_test_repeat':
        next_state = BotTypingHandler.repeat_start
    chosen_option = message.text.lower()
    right_answer = await bot_handler.get_state_info(state, 'right_answer')
    if chosen_option == right_answer:
        await bot_handler.type_reply(message, f"Correct! {emoji.emojize(':check_mark_button:')}",
                                     bot_handler.keyboards['next'])
        await increase_score(state)
    else:
        await bot_handler.type_reply(message, f"Oops, wrong answer! The correct word was <b>{right_answer}</b>",
                                     bot_handler.keyboards['next'])
    await state.set_state(next_state)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
