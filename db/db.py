import logging
import sqlite3
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv


class BotDB:
    logger = logging.getLogger("BotDB")

    def __init__(self, db_name, sql_script=None):
        self.db_name = db_name
        if not os.path.exists(self.db_name):
            if sql_script:
                self.create_db(sql_script)
            else:
                raise FileNotFoundError(f"Database file '{self.db_name}' does not exist and no SQL script provided.")

        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

    def create_db(self, sql_script_path):
        with open(sql_script_path, 'r', encoding='utf-8') as file:
            sql_script = file.read()
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.cursor.executescript(sql_script)
        self.conn.commit()
        self.conn.close()

    def insert_new_word(self, word, category, translation):
        word_uuid = uuid.uuid4()
        self.conn.execute(f'INSERT INTO words (id, word, category, translation, status)'
                          f'VALUES ("{word_uuid}","{word}", "{category}", "{translation}", "new");')
        self.conn.commit()
        return word_uuid

    def insert_new_test(self, word_id, status):
        test_uuid = uuid.uuid4()
        current_datetime = datetime.now()
        self.conn.execute(f'INSERT INTO tests (id, word_id, test_number, test_date)'
                          f'VALUES ("{test_uuid}","{word_id}", "{status}", "{current_datetime}");')
        self.conn.commit()

    def select_word_by_status(self, status):
        data = self.conn.execute(f"SELECT * FROM words WHERE status = '{status}' LIMIt 1;").fetchall()
        for row in data:
            word_id = row["id"]
            word = row["word"]
            category = row["category"]
            translation = row["translation"]
        return word_id, word, category, translation

    def update_word_status(self, word_id, status):
        self.conn.execute(f"UPDATE words SET status = '{status}' WHERE id = '{word_id}';")
        self.conn.commit()

    def select_all_by_word(self, word, category):
        word_data = self.conn.execute(f"SELECT * FROM words WHERE word = '{word}' AND category = '{category}' LIMIt 1;").fetchall()
        if word_data:
            for row in word_data:
                word_id = row["id"]
                word = row["word"]
                word_category = row["category"]
                word_status = row["status"]
            return word, word_category, word_status
        else:
            return None


if __name__ == "__main__":
    load_dotenv()
    db_name = os.getenv('DB_NAME')
    db = BotDB(db_name, 'db_creation.sql')
    db.insert_new_word('try', 'noun', 'пытаться, пробовать')
