import logging
import os
import random
import sqlite3
import uuid
from datetime import datetime, timedelta

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
            "id"	TEXT NOT NULL UNIQUE,
            "word"	TEXT NOT NULL,
            "category" TEXT NOT NULL,
            "status"	TEXT NOT NULL,
            "modified_date" TEXT NOT NULL,
            "user_id" TEXT NOT NULL,
            PRIMARY KEY("id")
        );
        CREATE TABLE "settings" (
            "user_id" TEXT NOT NULL UNIQUE,
            "daily_message_enabled" TEXT NOT NULL,
            "review_message_enabled" TEXT NOT NULL,
            PRIMARY KEY("user_id")
        );
        """
        cursor.executescript(sql_script)
        conn.commit()
        conn.close()
        self.logger.info("Database created successfully.")

    def insert_new_word(self, word, category, user_id):
        word_uuid = uuid.uuid4()
        current_datetime = datetime.now()
        self.conn.execute(f'INSERT INTO words (id, word, category, status, modified_date, user_id)'
                          f'VALUES ("{word_uuid}","{word}", "{category}", "New", "{current_datetime}", "{user_id}");')
        self.conn.commit()

    def select_words_by_status(self, status, user_id):
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
                    f"SELECT id, word, category FROM words WHERE status = '{chosen_status}' AND user_id = '{user_id}' LIMIt 1;").fetchall()
            if chosen_status == 'New':
                self.update_word_status(data[0][0], 'Acquainted')
            else:
                self.update_word_status(data[0][0], 'Familiar')
        elif status == 'New':
            data = self.conn.execute(
                f"SELECT id, word, category FROM words WHERE status = '{status}' AND user_id = '{user_id}' LIMIt 1;").fetchall()
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
                    f"SELECT id, word, category FROM words WHERE status = '{chosen_status}' AND user_id = '{user_id}' LIMIt 1;").fetchall()
            if chosen_status == 'Familiar':
                self.update_word_status(data[0][0], 'Reviewed')
            else:
                self.update_word_status(data[0][0], 'Memorized')
        return data[0][0], data[0][1], data[0][2], chosen_status

    def update_word_status(self, word_id, status):
        self.conn.execute(f"UPDATE words SET status = '{status}' WHERE id = '{word_id}';")
        self.conn.commit()

    def select_all_by_word(self, word, category, user_id):
        word_data = self.conn.execute(
            f"SELECT * FROM words WHERE word = '{word}' AND category = '{category}' AND user_id = '{user_id}' LIMIt 1;").fetchall()
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

    def select_random_row(self, category, user_id):
        if category == 'All':
            word_data = self.conn.execute(
                f"SELECT word FROM words WHERE user_id = '{user_id}' ORDER BY RANDOM() LIMIT 1").fetchone()
        else:
            word_data = self.conn.execute(
                f"SELECT word FROM words WHERE category = '{category}' AND user_id = '{user_id}' ORDER BY RANDOM() LIMIT 1").fetchone()
        return word_data[0]

    def select_count_by_category(self, category, user_id):
        count = self.conn.execute(
            f"SELECT COUNT(id) FROM words WHERE category = '{category}' AND user_id = '{user_id}';").fetchone()
        return count[0]

    def select_date_delta(self, user_id):
        latest_date_row = self.conn.execute(
            f"SELECT modified_date FROM words WHERE user_id = '{user_id}' ORDER BY modified_date DESC LIMIT 1;").fetchone()
        if latest_date_row:
            latest_date = datetime.strptime(latest_date_row[0], '%Y-%m-%d %H:%M:%S.%f')
            current_date = datetime.now()
            date_difference = current_date.date() - latest_date.date()
            if date_difference >= timedelta(days=1):
                return True
            else:
                return False
        else:
            return False

    def select_word_of_the_day(self, user_id):
        word_of_the_day = self.conn.execute(
            f"SELECT word, category FROM words WHERE user_id = '{user_id}' AND status <> 'New' ORDER BY RANDOM() DESC LIMIT 1;").fetchone()
        if word_of_the_day:
            return word_of_the_day[0], word_of_the_day[1]
        else:
            return False

if __name__ == "__main__":
    load_dotenv()
    # db_name = os.getenv('DB_NAME')
    db = DB()
    category = 'noun'
    # keyboard = list(set([db.select_random_row(category) for element in range(3)]))
    # print(keyboard)

    # print(db.select_words_by_status('Familiar/Reviewed'))
    # print(db.select_all_by_word_id('0c4a349b-439e-4f9f-90b6-1ddfadab9f99'))
    # print(db.select_count_by_category('Adjective'))
    print(db.select_word_of_the_day('320803022'))
    # print(db.select_all_by_word('trepidation', 'Noun'))
    # print(db.db_path)
