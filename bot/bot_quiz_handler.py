import random
from bot_typing_handler import BotTypingHandler
from dictionary.my_dictionary_collaboration import LanguageProcessing

bot_typer = BotTypingHandler()


async def choose_word_for_quiz(state):
    words_to_learn = await bot_typer.get_state_info(state, 'words_to_learn')
    try:
        words_selection = await bot_typer.get_state_info(state, 'words_selection')
    except KeyError:
        words_selection = {element: 0 for element in words_to_learn}
    max_selections = 1
    if all(count >= max_selections for count in words_selection.values()):
        return None
    min_count = min(words_selection.values())
    available_elements = [element for element, count in words_selection.items() if count == min_count]
    chosen_word = random.choice(available_elements)
    words_selection[chosen_word] += 1
    await state.update_data(words_selection=words_selection)
    return chosen_word


async def show_pick_contest(state, word_id, db, type):
    word_db_info = db.select_all_by_word_id(word_id)
    word = word_db_info[1]
    category = word_db_info[2]
    word_info = LanguageProcessing(word)
    if type == 'definitions':
        definitions = word_info.get_word_definitions(category)
        print_definitions = bot_typer.prepare_sentences_for_print(definitions, category)
    elif type == 'translations':
        translations = word_info.get_word_translations(category)
        print_definitions = bot_typer.prepare_sentences_for_print(None, category, translations)
    keyboard = [word]
    while len(keyboard) < 4:
        try:
            keyboard.append(db.select_random_row(category))
            keyboard = list(set(keyboard))
        except TypeError:
            keyboard.append(db.select_random_row(category))
            keyboard = list(set(keyboard))
    await state.update_data(right_answer=word)
    random.shuffle(keyboard)
    return print_definitions, keyboard
