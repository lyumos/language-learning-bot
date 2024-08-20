from aiogram import types
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ParseMode
import emoji
from dictionary.my_dictionary_collaboration import LanguageProcessing
from db.db import DB


class BotTypingHandler(StatesGroup):
    start_mode_choice = State()
    check_word_choice = State()
    repeat_words_choice = State()
    learn_words_choice = State()
    new_word_checking = State()
    new_word_printing = State()
    new_word_handling = State()
    test_start = State()
    check_test = State()
    repeat_start = State()
    check_test_repeat = State()
    settings_choice = State()

    def __init__(self, bot_db: DB):
        self.db = bot_db

    bot_texts = {
        'welcome': f"Hi {emoji.emojize(":vulcan_salute_light_skin_tone:")}\nYou can choose to: check a word, learn words you've added, or review words you've already learned",
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
        'quiz_time': f"That's all for now! Let's take a quiz {emoji.emojize(":rocket:")}",
        'settings': f"Settings are up! What would you like to modify?"
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
                 'happy_face': f"{emoji.emojize(":rocket:")}",
                 'next': [f"{emoji.emojize(":right_arrow:")}"],
                 'settings': ['Notifications', 'Word of the day', 'Quiz']
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
                elif isinstance(translations, list):
                    print_translations = '<i>' + ', '.join(translations).capitalize() + '</i>'
                    # capitalized = print_translations[0].upper() + print_translations[1:]
                    print_sentences.append(print_translations)
                return "\n".join(print_sentences)
            else:
                return ''

    async def type_word_info(self, message, state, choice, definitions=None):
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

    async def type_extra_info(self, message, state, mode):
        if mode == 'check':
            part_of_speech = await self.get_state_info(state, 'pt_of_speech')
            word = await self.get_state_info(state, 'word')

            word_info = LanguageProcessing(word)
            examples = word_info.get_word_examples(part_of_speech)
            print_examples = self.prepare_sentences_for_print(examples, part_of_speech)
            await state.update_data(examples=examples)
            audio_link = word_info.get_audio()
            if print_examples and audio_link:
                await self.type_reply(message, f"{print_examples}\n{audio_link}\n\nWhat's your next move?",
                                      self.keyboards['next_move'])
            elif print_examples and not audio_link:
                await self.type_reply(message, f"{print_examples}\n\nWhat's your next move?",
                                      self.keyboards['next_move'])
            else:
                await self.type_reply(message, self.bot_texts['no_examples_check'],
                                      self.keyboards['next_move'])
        else:
            if mode == 'learn':
                words = await self.get_state_info(state, 'words_to_learn')
            elif mode == 'repeat':
                words = await self.get_state_info(state, 'words_to_repeat')
            word_id = words[-1]
            word_db_info = self.db.select_all_by_word_id(word_id)
            word = word_db_info[1]
            category = word_db_info[2]
            word_info = LanguageProcessing(word)
            examples = word_info.get_word_examples(category)
            print_examples = self.prepare_sentences_for_print(examples, category)
            audio_link = word_info.get_audio()
            if print_examples and audio_link:
                await self.type_reply(message, f"{print_examples}\n{audio_link}",
                                      self.keyboards['show_next_word_no_advanced'])
            elif print_examples and not audio_link:
                await self.type_reply(message, f"{print_examples}",
                                      self.keyboards['show_next_word_no_advanced'])
            else:
                await self.type_reply(message, self.bot_texts['no_examples_learn'],
                                      self.keyboards['show_next_word_no_advanced'])