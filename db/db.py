import logging
import os
import random
import sqlite3
import uuid
from datetime import datetime

from dotenv import load_dotenv


class DB:
    logger = logging.getLogger("BotDB")

    def __init__(self):
        load_dotenv()

        self.db_dir = os.getenv('DB_DIR', './')
        self.dbname = os.getenv('DB_NAME', 'db.db')
        self.db_path = os.path.join(self.db_dir, self.dbname)

        if not os.path.exists(self.db_path):
            self.logger.info("Database does not exist. Creating a new one.")
            self.create_database()

        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def create_database(self):
        os.makedirs(self.db_dir, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        sql_script = """
        CREATE TABLE "words" (
            "id"    TEXT NOT NULL UNIQUE,
            "word"  TEXT NOT NULL,
            "category" TEXT NOT NULL,
            "status"    TEXT NOT NULL,
            PRIMARY KEY("id")
        );
        """
        cursor.executescript(sql_script)
        conn.commit()
        conn.close()
        self.logger.info("Database created successfully.")

    def insert_new_word(self, word, category):
        word_uuid = uuid.uuid4()
        self.conn.execute(f'INSERT INTO words (id, word, category, status)'
                          f'VALUES ("{word_uuid}","{word}", "{category}", "New");')
        self.conn.commit()

    def insert_new_test(self, word_id, status):
        test_uuid = uuid.uuid4()
        current_datetime = datetime.now()
        self.conn.execute(f'INSERT INTO tests (id, word_id, test_number, test_date)'
                          f'VALUES ("{test_uuid}","{word_id}", "{status}", "{current_datetime}");')
        self.conn.commit()

    def select_words_by_status(self, status):
        if status == 'New/Acquainted':
            statuses = ['New', 'Acquainted']
            data = None
            count = 10
            while not data:
                count -= 1
                if count < 0:
                    raise IndexError
                chosen_status = random.choice(statuses)
                data = self.conn.execute(
                    f"SELECT id, word, category FROM words WHERE status = '{chosen_status}' LIMIt 1;").fetchall()
            if chosen_status == 'New':
                self.update_word_status(data[0][0], 'Acquainted')
            else:
                self.update_word_status(data[0][0], 'Familiar')
        elif status == 'New':
            data = self.conn.execute(
                f"SELECT id, word, category FROM words WHERE status = '{status}' LIMIt 1;").fetchall()
            self.update_word_status(data[0][0], 'Acquainted')
            chosen_status = 'New'
        elif status == 'Familiar/Reviewed':
            statuses = ['Familiar', 'Reviewed']
            data = None
            count = 10
            while not data:
                count -= 1
                if count < 0:
                    raise IndexError
                chosen_status = random.choice(statuses)
                data = self.conn.execute(
                    f"SELECT id, word, category FROM words WHERE status = '{chosen_status}' LIMIt 1;").fetchall()
            if chosen_status == 'Familiar':
                self.update_word_status(data[0][0], 'Reviewed')
            else:
                self.update_word_status(data[0][0], 'Memorized')
        return data[0][0], data[0][1], data[0][2], chosen_status

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
    # db_name = os.getenv('DB_NAME')
    db = DB()
    category = 'noun'
    # keyboard = list(set([db.select_random_row(category) for element in range(3)]))
    # print(keyboard)

    print(db.select_words_by_status('Familiar/Reviewed'))
    # print(db.select_all_by_word_id('e9caa3db-e957-4f2b-922a-38074ec654ed'))
    # print(db.select_all_by_word('trepidation', 'Noun'))
    # print(db.db_path)
