from aiogram import types
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from dictionary.my_dictionary_collaboration import LanguageProcessing
import emoji
from aiogram.enums import ParseMode


class BotTypingHandler(StatesGroup):
    start_mode_choice = State()
    check_word_choice = State()
    repeat_words_choice = State()
    learn_words_choice = State()
    new_word_checking = State()
    new_word_printing = State()
    new_word_handling = State()
    test_start = State()

    bot_texts = {
        'welcome': f"Hi {emoji.emojize(":vulcan_salute_light_skin_tone:")}\nNeed something? Choose from: check my word, other options in progress",
        'word_check': f"Check my word {emoji.emojize(":magnifying_glass_tilted_left:")}",
        'writing_hand': f"{emoji.emojize(":writing_hand_light_skin_tone:")}",
        'wrong_word': f"Whoops, that's not a real word!\n\nLet's try again {emoji.emojize(":ghost:")}",
        'word_type': f"Pick a part of speech or go wild - choose 'em all!",
        'word_added': f"Word's in! Added this one to the vocabulary collection!",
        'no_examples_learn': f"Looks like there\'s nothing here!",
        'no_examples_check': f"Looks like there\'s nothing here!\n\nWhat's your next move?",
        'square_one': "Back to square one, eh? Let's start fresh!",
        'no_words_to_learn': f"Looks like there are no words to study right now!\n\nAdd new words to your vocabulary collection to study later {emoji.emojize(":books:")}",
        'words_ended': f"Those were all the new words! Add more to study later. Let's take the quiz {emoji.emojize(":rocket:")}",
        'quiz_time': f"That's all for now! Let's take a quiz {emoji.emojize(":rocket:")}"
    }

    keyboards = {'init': [f"Check my word {emoji.emojize(":magnifying_glass_tilted_left:")}",
                          f'Learn {emoji.emojize(":nerd_face:")}', 'Repeat'],
                 'next_move': [f"{emoji.emojize(":left_arrow:")}", f"{emoji.emojize(":thinking_face:")}",
                               f"{emoji.emojize(":plus:")}", f"{emoji.emojize(":repeat_button:")}",
                               f"{emoji.emojize(":chequered_flag:")}"],
                 'next_step': [f"{emoji.emojize(":right_arrow:")}", f"{emoji.emojize(":thinking_face:")}",
                               f"{emoji.emojize(":chequered_flag:")}"],
                 'show_next_word_no_advanced': [f"{emoji.emojize(":right_arrow:")}",
                                                f"{emoji.emojize(":chequered_flag:")}"],
                 'happy_face': f"{emoji.emojize(":partying_face:")}"
                 }

    @staticmethod
    def show_keyboard(items: list[str]) -> ReplyKeyboardMarkup:
        row = [KeyboardButton(text=item) for item in items]
        return ReplyKeyboardMarkup(keyboard=[row], resize_keyboard=True)

    @staticmethod
    async def get_state_info(state, item):
        data = await state.get_data()
        if data:
            return data[f'{item}']
        else:
            return None

    async def type_answer(self, message, answer, buttons=None):
        if buttons:
            await message.answer(
                text=f"{answer}",
                reply_markup=self.show_keyboard(buttons),
                parse_mode=ParseMode.HTML
            )
        else:
            await message.answer(
                text=f"{answer}",
                parse_mode=ParseMode.HTML
            )

    async def type_reply(self, message, reply, buttons=None):
        if buttons:
            await message.reply(
                text=f"{reply}",
                reply_markup=self.show_keyboard(buttons),
                parse_mode=ParseMode.HTML
            )
        else:
            await message.reply(
                text=f"{reply}",
                reply_markup=types.ReplyKeyboardRemove(),
                parse_mode=ParseMode.HTML
            )

    @staticmethod
    def prepare_sentences_for_print(sentences, choice, translations=None):
        if isinstance(sentences, list):
            print_sentences = [f"- {s.rstrip('.').capitalize()}" for s in sentences]
            if not translations:
                return f"<b>{choice.capitalize()}</b>:\n" + "\n".join(print_sentences)
            else:
                if isinstance(translations, list):
                    if len(translations) > 1:
                        return f"<b>{choice.capitalize()}</b>:\n" + "\n".join(
                            print_sentences) + '\n\n<i>' + f'{translations[0].capitalize()}' + ', ' + ', '.join(
                            translations[1:]) + '</i>'
                    else:
                        return f"<b>{choice.capitalize()}</b>:\n" + "\n".join(
                            print_sentences) + '\n\n<i>' + f'{translations[0].capitalize()}' + '</i>'
                elif isinstance(translations, str):
                    return f"<b>{choice.capitalize()}</b>:\n" + "\n".join(
                        print_sentences) + f'<i>\n\n{translations.capitalize()}</i>'
        elif isinstance(sentences, dict):
            print_sentences = []
            for key in sentences.keys():
                print_sentences.append(f"\n<b>{key.capitalize()}:</b>")
                for key_, value in sentences.items():
                    if key == key_:
                        print_sentences += [f"- {s.rstrip('.').capitalize()}" for s in value]
                        if translations:
                            if isinstance(translations, dict):
                                if key in translations.keys():
                                    if len(translations[key]) > 1:
                                        print_translations = '\n<i>' + translations[key][
                                            0].capitalize() + ', ' + ', '.join(translations[key][1:]) + '</i>'
                                    else:
                                        print_translations = '\n<i>' + translations[key][0].capitalize() + '</i>'
                                    print_sentences.append(print_translations)
                                else:
                                    pass
                            elif isinstance(translations, str):
                                print_translations = '\n<i>' + translations.capitalize() + '</i>'
                                print_sentences.append(print_translations)
            return "\n".join(print_sentences)
        elif not sentences:
            if translations:
                print_sentences = []
                if isinstance(translations, dict):
                    for key in translations.keys():
                        if len(translations[key]) > 1:
                            print_translations = '<i>' + translations[key][0].capitalize() + ', ' + ', '.join(
                                translations[key][1:]) + '</i>'
                        else:
                            print_translations = '\n<i>' + translations[key][0].capitalize() + '</i>'
                        print_sentences.append(print_translations)
                elif isinstance(translations, str):
                    print_translations = '<i>' + translations.capitalize() + '</i>'
                    print_sentences.append(print_translations)
                return "\n".join(print_sentences)
            else:
                return ''

    async def type_new_word_info(self, message, state, choice, definitions=None):
        new_word = await self.get_state_info(state, 'word')
        word = LanguageProcessing(new_word)
        if definitions:
            definitions = word.get_word_definitions(choice)
            translation = word.get_word_translations(choice)
            print_definitions = self.prepare_sentences_for_print(definitions, choice, translation)
            await state.update_data(en_definitions=definitions)
            await state.update_data(ru_translations=translation)
            await self.type_reply(message, f"{print_definitions}\n\nWhat's your next move?",
                                  self.keyboards['next_move'])
        else:
            translation = word.get_word_translations(choice)
            await state.update_data(ru_translations=translation)
            await state.update_data(en_definitions=None)
            print_definitions = self.prepare_sentences_for_print(None, choice, translation)
            await self.type_reply(message, f"{print_definitions}\n\nWhat's your next move?",
                                  self.keyboards['next_move'])

    async def type_advanced_info(self, message, state, db=None):
        if not db:
            part_of_speech = await self.get_state_info(state, 'pt_of_speech')
            word = await self.get_state_info(state, 'word')

            word_info = LanguageProcessing(word)
            examples = word_info.get_word_examples(part_of_speech)
            print_examples = self.prepare_sentences_for_print(examples, part_of_speech)
            await state.update_data(examples=examples)
            if print_examples:
                await self.type_reply(message, f"{print_examples}\n\nWhat's your next move?",
                                      self.keyboards['next_move'])
            else:
                await self.type_reply(message, self.bot_texts['no_examples_check'],
                                      self.keyboards['next_move'])
        else:
            words_to_learn = await self.get_state_info(state, 'words_to_learn')
            word_id = words_to_learn[-1]
            word_db_info = db.select_all_by_word_id(word_id)
            word = word_db_info[1]
            category = word_db_info[2]
            word_info = LanguageProcessing(word)
            examples = word_info.get_word_examples(category)
            print_examples = self.prepare_sentences_for_print(examples, category)
            if print_examples:
                await self.type_reply(message, f"{print_examples}", self.keyboards['show_next_word_no_advanced'])
            else:
                await self.type_reply(message, self.bot_texts['no_examples_learn'],
                                      self.keyboards['show_next_word_no_advanced'])

    async def add_word_to_db(self, message, state, db):
        new_word = await self.get_state_info(state, 'word')
        category = await self.get_state_info(state, 'pt_of_speech')
        word_data = db.select_all_by_word(new_word, category.title())
        # Если такое слово еще не добавлено в БД
        if word_data is None:
            if category.title() == 'All':
                parts_of_speech = await self.get_state_info(state, 'parts_of_speech')
                for part in parts_of_speech:
                    if part != 'All':
                        db.insert_new_word(new_word, part.title())
            else:
                db.insert_new_word(new_word, category.title())
            await self.type_reply(message, self.bot_texts['word_added'], self.keyboards['init'])

        else:
            await self.type_reply(message,
                                  f"Already in your vocabulary collection!\n\nWord: {word_data[1]}\nCategory: {word_data[2]}\nStatus: {word_data[3]}\n\nLet's try again {emoji.emojize(":ghost:")}",
                                  self.keyboards['init'])

    async def print_words_to_learn(self, message, state, words_to_learn, db, flag):
        try:
            word_id, word, category = db.select_words_by_status('New')
            words_to_learn.append(word_id)
            await state.update_data(words_to_learn=words_to_learn)

            word_obj = LanguageProcessing(word)
            definitions = word_obj.get_word_definitions(category)
            translation = word_obj.get_word_translations(category)
            print_definitions = self.prepare_sentences_for_print(definitions, category, translation)
            await self.type_reply(message, f"<b>{word}</b>\n\n{print_definitions}",
                                  self.keyboards['next_step'])
            await state.set_state(BotTypingHandler.learn_words_choice)
        except IndexError:
            if flag == 0:
                await self.type_reply(message, self.bot_texts['no_words_to_learn'],
                                      self.keyboards['init'])
                await state.set_state(BotTypingHandler.start_mode_choice)
            else:
                await self.type_reply(message, self.bot_texts['words_ended'], self.keyboards['happy_face'])
                await state.set_state(BotTypingHandler.test_start)
