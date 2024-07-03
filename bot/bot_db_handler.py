from bot_typing_handler import BotTypingHandler
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
        word_data = self.db.select_all_by_word(new_word, category.title())
        # Если такое слово еще не добавлено в БД
        if word_data is None:
            if category.title() == 'All':
                parts_of_speech = await self.bot_typer.get_state_info(state, 'parts_of_speech')
                for part in parts_of_speech:
                    if part != 'All':
                        self.db.insert_new_word(new_word, part.title())
            else:
                self.db.insert_new_word(new_word, category.title())
            await self.bot_typer.type_reply(message, self.bot_typer.bot_texts['word_added'],
                                            self.bot_typer.keyboards['init'])

        else:
            await self.bot_typer.type_reply(message,
                                            f"Already in your vocabulary collection!\n\nWord: {word_data[1]}\nCategory: {word_data[2]}\nStatus: {word_data[3]}\n\nLet's try again {emoji.emojize(":ghost:")}",
                                            self.bot_typer.keyboards['init'])
