import random
from bot_typing_handler import BotTypingHandler
from dictionary.my_dictionary_collaboration import LanguageProcessing

bot_typer = BotTypingHandler()


async def show_pick_contest(state, word_id, db):
    quiz_mode = ['definitions', 'translations', 'examples']
    chosen_mode = random.choice(quiz_mode)
    word_db_info = db.select_all_by_word_id(word_id)
    word = word_db_info[1]
    category = word_db_info[2]
    word_info = LanguageProcessing(word)
    if chosen_mode == 'definitions':
        definitions = word_info.get_word_definitions(category)
        print_definitions = bot_typer.prepare_sentences_for_print(definitions, category)
    elif chosen_mode == 'translations':
        translations = word_info.get_word_translations(category)
        if translations:
            print_definitions = bot_typer.prepare_sentences_for_print(None, category, translations)
        else:
            definitions = word_info.get_word_definitions(category)
            print_definitions = bot_typer.prepare_sentences_for_print(definitions, category)
    elif chosen_mode == 'examples':
        examples = word_info.get_word_examples(category)
        if examples:
            replaced_examples = [sentence.replace(word, '______') for sentence in examples]
            print_definitions = bot_typer.prepare_sentences_for_print(replaced_examples, category)
        else:
            definitions = word_info.get_word_definitions(category)
            print_definitions = bot_typer.prepare_sentences_for_print(definitions, category)
    keyboard = [word]
    while len(keyboard) < 4:
        try:
            keyboard.append(db.select_random_row(category))
            keyboard = list(set(keyboard))
            if len(keyboard) == 1:
                while len(keyboard) < 4:
                    keyboard.append(db.select_random_row('All'))
                    keyboard = list(set(keyboard))
                break
        except TypeError:
            keyboard.append(db.select_random_row(category))
            keyboard = list(set(keyboard))
    await state.update_data(right_answer=word)
    random.shuffle(keyboard)
    return print_definitions, keyboard


async def increase_score(state):
    try:
        score = await bot_typer.get_state_info(state, 'learning_score')
    except KeyError:
        score = 0
    score += 1
    await state.update_data(learning_score=score)


async def print_score(state, message):
    max_score = await bot_typer.get_state_info(state, 'total_score')
    try:
        current_score = await bot_typer.get_state_info(state, 'learning_score')
        if current_score / max_score < 0.34:
            await bot_typer.type_reply(message,
                                       f"Don't worry, you can do better next time! Keep practicing and you'll see improvement. Your score is {current_score}/{max_score}.",
                                       bot_typer.keyboards['init'])
        elif current_score / max_score < 0.64:
            await bot_typer.type_reply(message,
                                       f"Nice effort! You're getting there. Keep it up and you'll continue to improve. Your score is {current_score}/{max_score}.",
                                       bot_typer.keyboards['init'])
        else:
            await bot_typer.type_reply(message,
                                       f"Great job! That was a fantastic round. Your score is {current_score}/{max_score}.",
                                       bot_typer.keyboards['init'])
    except KeyError:
        await bot_typer.type_reply(message,
                                   f"Don't worry, you can do better next time! Keep practicing and you'll see improvement. Your score is 0/{max_score}.",
                                   bot_typer.keyboards['init'])


async def buffer_clear_out(state, mode):
    if mode == 'learn':
        words_key = 'words_to_learn'
        selection_key = 'words_selection'
    else:  # mode == 'repeat'
        words_key = 'words_to_repeat'
        selection_key = 'words_selection_repeat'

    await state.update_data(**{words_key: []})
    await state.update_data(**{selection_key: {}})
    await state.update_data(learning_score=0)


async def choose_word_for_quiz(state, mode):
    if mode == 'learn':
        words_key = 'words_to_learn'
        selection_key = 'words_selection'
    else:  # mode == 'repeat'
        words_key = 'words_to_repeat'
        selection_key = 'words_selection_repeat'
    words = await bot_typer.get_state_info(state, words_key)
    try:
        words_selection = await bot_typer.get_state_info(state, selection_key)
        if words_selection == {}:
            words_selection = {element: 0 for element in words}
    except KeyError:
        words_selection = {element: 0 for element in words}

    max_selections = 1
    total_score = len(words_selection) * max_selections
    await state.update_data(total_score=total_score)

    if all(count >= max_selections for count in words_selection.values()):
        return None

    min_count = min(words_selection.values())
    available_elements = [element for element, count in words_selection.items() if count == min_count]
    chosen_word = random.choice(available_elements)
    words_selection[chosen_word] += 1
    await state.update_data(**{selection_key: words_selection})
    return chosen_word
