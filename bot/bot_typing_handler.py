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

    bot_texts = {
        'welcome': f"Hi {emoji.emojize(":vulcan_salute_light_skin_tone:")}\nNeed something? Choose from: check my word, other options in progress",
        'word_check': f"Check my word {emoji.emojize(":magnifying_glass_tilted_left:")}",
        'writing_hand': f"{emoji.emojize(":writing_hand_light_skin_tone:")}",
        'wrong_word': f"Whoops, that's not a real word!\n\nLet's try again {emoji.emojize(":ghost:")}",
        'word_type': f"Pick a part of speech or go wild - choose 'em all!",
        'word_added': f"Word's in! Added this one to the vocabulary collection!",
        'square_one': "Back to square one, eh? Let's start fresh!"
    }

    keyboards = {'init': [f"Check my word {emoji.emojize(":magnifying_glass_tilted_left:")}", 'Learn', 'Repeat'],
                 'next_move': [f"{emoji.emojize(":left_arrow:")}", f"{emoji.emojize(":thinking_face:")}",
                               f"{emoji.emojize(":plus:")}", f"{emoji.emojize(":repeat_button:")}",
                               f"{emoji.emojize(":chequered_flag:")}"],
                 'next_step': [f"{emoji.emojize(":right_arrow:")}", f"{emoji.emojize(":thinking_face:")}", f"{emoji.emojize(":chequered_flag:")}"]
                 }

    @staticmethod
    def show_keyboard(items: list[str]) -> ReplyKeyboardMarkup:
        row = [KeyboardButton(text=item) for item in items]
        return ReplyKeyboardMarkup(keyboard=[row], resize_keyboard=True)

    @staticmethod
    async def get_state_info(state, item):
        data = await state.get_data()
        return data[f'{item}']

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

    async def type_answer(self, message, answer, buttons=None):
        if buttons:
            await message.answer(
                text=f"{answer}",
                reply_markup=self.show_keyboard(buttons)
            )
        else:
            await message.answer(
                text=f"{answer}"
            )

    async def type_reply(self, message, reply, buttons=None):
        if buttons:
            await message.reply(
                text=f"{reply}",
                reply_markup=self.show_keyboard(buttons)
            )
        else:
            await message.reply(
                text=f"{reply}",
                reply_markup=types.ReplyKeyboardRemove(),
            )

    async def type_new_word_info(self, message, state, choice, definitions=None):
        new_word = await self.get_state_info(state, 'word')
        word = LanguageProcessing(new_word)
        if definitions:
            definitions = word.get_word_definitions(choice)
            translation = word.get_word_translations(choice)
            print_definitions = self.prepare_sentences_for_print(definitions, choice, translation)
            await state.update_data(en_definitions=definitions)
            await state.update_data(ru_translations=translation)
            await message.reply(
                text=f"{print_definitions}\n\nWhat's your next move?",
                reply_markup=self.show_keyboard(self.keyboards['next_move']),
                parse_mode=ParseMode.HTML
            )
        else:
            translation = word.get_word_translations(choice)
            await state.update_data(ru_translations=translation)
            await state.update_data(en_definitions=None)
            print_definitions = self.prepare_sentences_for_print(None, choice, translation)
            await message.reply(
                text=f"{print_definitions}\n\nWhat's your next move?",
                reply_markup=self.show_keyboard(self.keyboards['next_move']),
                parse_mode=ParseMode.HTML
            )

    async def type_advanced_info(self, message, state):
        part_of_speech = await self.get_state_info(state, 'pt_of_speech')
        word = await self.get_state_info(state, 'word')
        word_info = LanguageProcessing(word)
        # relations = word_info.get_relations(part_of_speech)
        examples = word_info.get_word_examples(part_of_speech)
        print_examples = self.prepare_sentences_for_print(examples, part_of_speech)
        await state.update_data(examples=examples)
        # await state.update_data(relations=relations)
        if print_examples:
            await message.reply(
                text=f"{print_examples}\n\nWhat's your next move?",
                reply_markup=self.show_keyboard(self.keyboards['next_move']),
                parse_mode=ParseMode.HTML
            )
        else:
            await message.reply(
                text=f"Looks like there\'s nothing here!\n\nWhat's your next move?",
                reply_markup=self.show_keyboard(self.keyboards['next_move']),
                parse_mode=ParseMode.HTML
            )

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
                        new_word_id = db.insert_new_word(new_word, part.title())
            else:
                new_word_id = db.insert_new_word(new_word, category.title())
            await self.type_reply(message, self.bot_texts['word_added'], self.keyboards['init'])
            await state.set_state(BotTypingHandler.start_mode_choice)
        else:
            await message.reply(
                text=f"Already in your vocabulary collection!\n\nWord: {word_data[1]}\nCategory: {word_data[2]}\nStatus: {word_data[3]}\n\nLet's try again {emoji.emojize(":ghost:")}",
                reply_markup=self.show_keyboard(self.keyboards['init'])
            )
            await state.set_state(BotTypingHandler.start_mode_choice)


if __name__ == '__main__':
    my_dict = {'Noun': ['An attempt.', 'An act of tasting or sampling.',
                        'A score in rugby league and rugby union, analogous to a touchdown in American football.',
                        'A screen, or sieve, for grain.', 'an effort to accomplish something; an attempt.',
                        'an act of touching the ball down behind the opposing goal line, scoring points and entitling the scoring side to a goal kick.'],
               'Verb': ['To attempt; to endeavour. Followed by infinitive.', 'To divide; to separate.',
                        'To test, to work out.', 'To experiment, to strive.',
                        'make an attempt or effort to do something.', 'subject (someone) to trial.',
                        'make severe demands on (a person or a quality, typically patience).',
                        'smooth (roughly planed wood) with a plane to give an accurately flat surface.']}
    my_list = ['An attempt.', 'An act of tasting or sampling.',
               'A score in rugby league and rugby union, analogous to a touchdown in American football.']
    translations = {'Noun': ['попытка', 'испытание', 'проба'],
                    'Verb': ['пытаться', 'стараться', 'пробовать', 'отведать', 'судить', 'испытывать', 'добиваться',
                             'перепробовать', 'подвергать испытанию', 'допрашивать', 'расследовать', 'силиться',
                             'мучить', 'проверять на опыте', 'очищать', 'отведывать', 'порываться',
                             'ставить своей целью', 'утомлять', 'удручать', 'раздражать', 'вытапливать']}
    test = BotTypingHandler()
    print(test.prepare_sentences_for_print(my_dict, 'All', translations))
