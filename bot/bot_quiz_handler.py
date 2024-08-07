import random
from bot.bot_typing_handler import BotTypingHandler
from bot.bot_db_handler import BotDBHandler
from db.db import DB
from dictionary.my_dictionary_collaboration import LanguageProcessing


class BotQuizHandler:
    def __init__(self, bot_typer: BotTypingHandler, db_handler: BotDBHandler, bot_db: DB):
        self.bot_typer = bot_typer
        self.db_handler = db_handler
        self.db = bot_db

    async def choose_word_for_quiz(self, state, mode):
        if mode == 'learn':
            words_key = 'words_to_learn'
            selection_key = 'words_selection'
        else:  # mode == 'repeat'
            words_key = 'words_to_repeat'
            selection_key = 'words_selection_repeat'
        words = await self.bot_typer.get_state_info(state, words_key)
        try:
            words_selection = await self.bot_typer.get_state_info(state, selection_key)
            if words_selection == {}:
                words_selection = {element: 0 for element in words}
        except KeyError:
            words_selection = {element: 0 for element in words}

        max_selections = 3
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

    async def print_quiz_words(self, mode, message, state, words_list, flag):
        try:
            if mode == 'learn':
                word_status = 'New/Acquainted'
                next_state = BotTypingHandler.learn_words_choice
            else:  # mode == 'repeat'
                word_status = 'Familiar/Reviewed'
                next_state = BotTypingHandler.repeat_words_choice
            word_id, word, category, chosen_status = self.db.select_words_by_status(word_status)
            self.db.update_word_status(word_id, 'Shown')
            if len(words_list) == 0:
                old_statuses = {}
                await state.update_data(old_statuses=old_statuses)
            old_statuses = await self.bot_typer.get_state_info(state, 'old_statuses')
            old_statuses[f'{word_id}'] = chosen_status
            await state.update_data(old_statuses=old_statuses)
            words_list.append(word_id)
            await state.update_data(**{f'words_to_{mode}': words_list})

            word_obj = LanguageProcessing(word)
            definitions = word_obj.get_word_definitions(category)
            translation = word_obj.get_word_translations(category)
            print_definitions = self.bot_typer.prepare_sentences_for_print(definitions, category, translation)
            await self.bot_typer.type_reply(message, f"<b>{word}</b>\n\n{print_definitions}",
                                            self.bot_typer.keyboards['next_step'])
            await state.set_state(next_state)
        except IndexError:
            if flag == 0:
                await self.bot_typer.type_reply(message, self.bot_typer.bot_texts['no_words_to_learn'],
                                                self.bot_typer.keyboards['init'])
                await state.set_state(BotTypingHandler.start_mode_choice)
            else:
                await self.db_handler.revert_statuses(state)
                await self.bot_typer.type_reply(message, self.bot_typer.bot_texts['quiz_time'],
                                                self.bot_typer.keyboards['happy_face'])
                if mode == 'learn':
                    await state.set_state(BotTypingHandler.test_start)
                else:
                    await state.set_state(BotTypingHandler.repeat_start)

    async def get_exercise(self, state, word_id):
        exercise_mode = ['definitions', 'translations', 'examples']
        input_mode = ['buttons', 'typing']
        chosen_exercise = random.choice(exercise_mode)
        chosen_input = random.choice(input_mode)
        word_db_info = self.db.select_all_by_word_id(word_id)
        word = word_db_info[1]
        category = word_db_info[2]
        word_info = LanguageProcessing(word)
        if chosen_exercise == 'definitions':
            definitions = word_info.get_word_definitions(category)
            print_definitions = self.bot_typer.prepare_sentences_for_print(definitions, category)
        elif chosen_exercise == 'translations':
            translations = word_info.get_word_translations(category)
            if translations:
                print_definitions = self.bot_typer.prepare_sentences_for_print(None, category, translations)
            else:
                definitions = word_info.get_word_definitions(category)
                print_definitions = self.bot_typer.prepare_sentences_for_print(definitions, category)
        elif chosen_exercise == 'examples':
            examples = word_info.get_word_examples(category)
            if examples:
                replaced_examples = [sentence.replace(word, '______') for sentence in examples]
                print_definitions = self.bot_typer.prepare_sentences_for_print(replaced_examples, category)
            else:
                definitions = word_info.get_word_definitions(category)
                print_definitions = self.bot_typer.prepare_sentences_for_print(definitions, category)
        if chosen_input == 'buttons':
            keyboard = [word]
            while len(keyboard) < 4:
                try:
                    keyboard.append(self.db.select_random_row(category))
                    keyboard = list(set(keyboard))
                    if len(keyboard) == 1:
                        while len(keyboard) < 4:
                            keyboard.append(self.db.select_random_row('All'))
                            keyboard = list(set(keyboard))
                        break
                except TypeError:
                    keyboard.append(self.db.select_random_row(category))
                    keyboard = list(set(keyboard))
            random.shuffle(keyboard)
        else:
            keyboard = None
        await state.update_data(right_answer=word)
        return print_definitions, keyboard

    async def increase_score(self, state):
        try:
            score = await self.bot_typer.get_state_info(state, 'learning_score')
        except KeyError:
            score = 0
        score += 1
        await state.update_data(learning_score=score)

    async def print_score(self, state, message):
        max_score = await self.bot_typer.get_state_info(state, 'total_score')
        try:
            current_score = await self.bot_typer.get_state_info(state, 'learning_score')
            if current_score / max_score < 0.34:
                await self.bot_typer.type_reply(message,
                                                f"Don't worry, you can do better next time! Keep practicing and you'll see improvement. Your score is {current_score}/{max_score}.",
                                                self.bot_typer.keyboards['init'])
            elif current_score / max_score < 0.64:
                await self.bot_typer.type_reply(message,
                                                f"Nice effort! You're getting there. Keep it up and you'll continue to improve. Your score is {current_score}/{max_score}.",
                                                self.bot_typer.keyboards['init'])
            else:
                await self.bot_typer.type_reply(message,
                                                f"Great job! That was a fantastic round. Your score is {current_score}/{max_score}.",
                                                self.bot_typer.keyboards['init'])
        except KeyError:
            await self.bot_typer.type_reply(message,
                                            f"Don't worry, you can do better next time! Keep practicing and you'll see improvement. Your score is 0/{max_score}.",
                                            self.bot_typer.keyboards['init'])

    @staticmethod
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
