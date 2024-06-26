import logging
import sqlite3
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv
import random


class BotDB:
    logger = logging.getLogger("BotDB")

    def __init__(self, db_name):
        self.db_name = db_name
        script_dir = os.path.dirname(os.path.abspath(__file__))
        db_dir = os.path.abspath(os.path.join(script_dir, '../db'))
        self.db_path = os.path.join(db_dir, db_name)
        self.script_path = os.path.join(script_dir, 'db_creation.sql')
        self.logger.debug(f"Database path set to: {self.db_path}")
        self.logger.debug(f"SQL script path set to: {self.script_path}")
        if not os.path.exists(self.db_path):
            self.create_db()
        os.chdir(db_dir)
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

    def create_db(self):
        if not os.path.exists(self.script_path):
            raise FileNotFoundError(f"SQL script file '{self.script_path}' does not exist.")
        self.logger.info(f"Creating database at {self.db_path} using script {self.script_path}")
        with open(self.script_path, 'r', encoding='utf-8') as file:
            sql_script = file.read()
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.cursor.executescript(sql_script)
        self.conn.commit()
        self.conn.close()

    def insert_new_word(self, word, category):
        word_uuid = uuid.uuid4()
        self.conn.execute(f'INSERT INTO words (id, word, category, status)'
                          f'VALUES ("{word_uuid}","{word}", "{category}", "New");')
        self.conn.commit()
        # return word_uuid

    def insert_new_test(self, word_id, status):
        test_uuid = uuid.uuid4()
        current_datetime = datetime.now()
        self.conn.execute(f'INSERT INTO tests (id, word_id, test_number, test_date)'
                          f'VALUES ("{test_uuid}","{word_id}", "{status}", "{current_datetime}");')
        self.conn.commit()

    def select_words_by_status(self, status):
        if status == 'New/Acquainted':
            statuses = ['New', 'Acquainted']
            chosen_status = random.choice(statuses)
            data = self.conn.execute(
                f"SELECT id, word, category FROM words WHERE status = '{chosen_status}' LIMIt 1;").fetchall()
            if chosen_status == 'New':
                self.update_word_status(data[0][0], 'Acquainted')
            else:
                self.update_word_status(data[0][0], 'Familiar')
        elif status == 'New':
            data = self.conn.execute(f"SELECT id, word, category FROM words WHERE status = '{status}' LIMIt 1;").fetchall()
            self.update_word_status(data[0][0], 'Acquainted')
        elif status == 'Familiar/Reviewed':
            data = self.conn.execute(
                f"SELECT id, word, category FROM words WHERE status = '{status}' LIMIt 1;").fetchall()
            if status == 'Familiar':
                self.update_word_status(data[0][0], 'Reviewed')
            else:
                self.update_word_status(data[0][0], 'Memorized')
        return data[0][0], data[0][1], data[0][2]

    def update_word_status(self, word_id, status):
        self.conn.execute(f"UPDATE words SET status = '{status}' WHERE id = '{word_id}';")
        self.conn.commit()

    def select_all_by_word(self, word, category):
        word_data = self.conn.execute(
            f"SELECT * FROM words WHERE word = '{word}' AND category = '{category}' LIMIt 1;").fetchall()
        if word_data:
            return word_data[0][0], word_data[0][1], word_data[0][2], word_data[0][3]
        else:
            return None

    def select_all_by_word_id(self, id):
        word_data = self.conn.execute(
            f"SELECT * FROM words WHERE id = '{id}';").fetchone()
        if word_data:
            return word_data
        else:
            return None

    def select_random_row(self, category):
        if category == 'All':
            word_data = self.conn.execute(
                f"SELECT word FROM words ORDER BY RANDOM() LIMIT 1").fetchone()
        else:
            word_data = self.conn.execute(
                f"SELECT word FROM words WHERE category = '{category}' ORDER BY RANDOM() LIMIT 1").fetchone()
        return word_data[0]


if __name__ == "__main__":
    load_dotenv()
    db_name = os.getenv('DB_NAME')
    db = BotDB(db_name)
    category = 'noun'
    keyboard = list(set([db.select_random_row(category) for element in range(3)]))
    print(keyboard)
    # print(db.select_all_by_word_id('e9caa3db-e957-4f2b-922a-38074ec654ed'))
    # print(db.select_all_by_word('trepidation', 'Noun'))
    # print(db.db_path)
