from bot.bot_typing_handler import BotTypingHandler
from db.db import DB
import emoji


class BotDBHandler:

    def __init__(self, bot_typer: BotTypingHandler, bot_db: DB):
        self.bot_typer = bot_typer
        self.db = bot_db

    async def revert_statuses(self, state):
        old_statuses = await self.bot_typer.get_state_info(state, 'old_statuses')
        for word_id, status in old_statuses.items():
            if status == 'New':
                self.db.update_word_status(word_id, 'Acquainted')
            elif status == 'Acquainted':
                self.db.update_word_status(word_id, 'Familiar')
            elif status == 'Familiar':
                self.db.update_word_status(word_id, 'Reviewed')
            elif status == 'Reviewed':
                self.db.update_word_status(word_id, 'Memorized')
        old_statuses = {}
        await state.update_data(old_statuses=old_statuses)

    async def add_word_to_db(self, message, state):
        new_word = await self.bot_typer.get_state_info(state, 'word')
        category = await self.bot_typer.get_state_info(state, 'pt_of_speech')
        if category.title() == 'All':
            count = 0
            parts_of_speech = await self.bot_typer.get_state_info(state, 'parts_of_speech')
            for available_category in parts_of_speech:
                if available_category != 'All':
                    word_data = self.db.select_all_by_word(new_word, available_category.title(),
                                                           user_id=str(message.from_user.id))
                    if not word_data:
                        count += 1
                        self.db.insert_new_word(new_word, available_category.title(), user_id=str(message.from_user.id))
            if count == 0:
                await self.bot_typer.type_reply(message,
                                                f"Already in your vocabulary collection!\n\nWord: {word_data[1]}\nCategory: {word_data[2]}\nStatus: {word_data[3]}\n\nLet's try again {emoji.emojize(":ghost:")}",
                                                self.bot_typer.keyboards['init'])
            else:
                await self.bot_typer.type_reply(message, self.bot_typer.bot_texts['word_added'],
                                                self.bot_typer.keyboards['init'])
        else:
            word_data = self.db.select_all_by_word(new_word, category.title(), user_id=str(message.from_user.id))
            # Если такое слово еще не добавлено в БД
            if word_data is None:
                if category.title() == 'All':
                    parts_of_speech = await self.bot_typer.get_state_info(state, 'parts_of_speech')
                    for part in parts_of_speech:
                        if part != 'All':
                            self.db.insert_new_word(new_word, part.title(), user_id=str(message.from_user.id))
                else:
                    self.db.insert_new_word(new_word, category.title(), user_id=str(message.from_user.id))
                await self.bot_typer.type_reply(message, self.bot_typer.bot_texts['word_added'],
                                                self.bot_typer.keyboards['init'])
            else:
                await self.bot_typer.type_reply(message,
                                                f"Already in your vocabulary collection!\n\nWord: {word_data[1]}\nCategory: {word_data[2]}\nStatus: {word_data[3]}\n\nLet's try again {emoji.emojize(":ghost:")}",
                                                self.bot_typer.keyboards['init'])

    async def modify_settings(self, user_id, setting, choice):
        self.db.update_settings(user_id, setting, choice)

    async def add_user_settings(self, user_id):
        self.db.insert_user_settings(user_id)

    async def get_stats(self, user_id):
        words_count = self.db.select_stats(user_id)
        return words_count

    async def check_lost_words(self):
        self.db.select_shown_words()
