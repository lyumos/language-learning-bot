import logging
import os
import random
import uuid
from datetime import datetime, timedelta
import psycopg2
from dotenv import load_dotenv


class DB:
    logger = logging.getLogger("BotDB")

    def __init__(self):
        load_dotenv()

        self.db_name = os.getenv('POSTGRES_DB')
        self.db_user = os.getenv('POSTGRES_USER')
        self.db_password = os.getenv('POSTGRES_PASSWORD')
        self.db_host = os.getenv('DB_HOST')

        self.conn = psycopg2.connect(
            dbname=self.db_name,
            user=self.db_user,
            password=self.db_password,
            host=self.db_host
        )
        self.cursor = self.conn.cursor()

        self.logger.info("Connected to PostgreSQL database.")
        self.create_database()

    def create_database(self):
        sql_script = """
        CREATE TABLE IF NOT EXISTS words (
            id UUID PRIMARY KEY,
            word TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT NOT NULL,
            modified_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            user_id TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS settings (
            user_id TEXT PRIMARY KEY,
            daily_reminder TEXT NOT NULL DEFAULT 'enabled',
            word_of_the_day TEXT NOT NULL DEFAULT 'enabled'
        );
        """
        self.cursor.execute(sql_script)
        self.conn.commit()
        self.logger.info("Database structure created successfully.")

    def insert_new_word(self, word, category, user_id):
        word_uuid = str(uuid.uuid4())
        current_datetime = datetime.now()
        self.cursor.execute(
            'INSERT INTO words (id, word, category, status, modified_date, user_id) VALUES (%s, %s, %s, %s, %s, %s);',
            (word_uuid, word, category, "New", current_datetime, user_id)
        )
        self.conn.commit()

    def insert_user_settings(self, user_id):
        self.cursor.execute(
            "SELECT user_id FROM settings WHERE user_id = %s;", (user_id,)
        )
        user_info = self.cursor.fetchone()
        if not user_info:
            self.cursor.execute(
                'INSERT INTO settings (user_id, daily_reminder, word_of_the_day) VALUES (%s, %s, %s);',
                (user_id, "enabled", "enabled")
            )
            self.conn.commit()

    def select_words_by_status(self, status, user_id):
        data = None
        chosen_status = None
        count = 10

        if status == 'New/Acquainted':
            statuses = ['New', 'Acquainted']
            while not data and count > 0:
                chosen_status = random.choice(statuses)
                self.cursor.execute(
                    f"SELECT id, word, category FROM words WHERE status = %s AND user_id = %s ORDER BY RANDOM() LIMIT 1;",
                    (chosen_status, user_id)
                )
                data = self.cursor.fetchall()
                count -= 1
            if chosen_status == 'New':
                self.update_word_status(data[0][0], 'Acquainted')
            else:
                self.update_word_status(data[0][0], 'Familiar')

        elif status == 'New':
            self.cursor.execute(
                f"SELECT id, word, category FROM words WHERE status = %s AND user_id = %s ORDER BY RANDOM() LIMIT 1;",
                ('New', user_id)
            )
            data = self.cursor.fetchall()
            self.update_word_status(data[0][0], 'Acquainted')

        elif status == 'Familiar/Reviewed':
            statuses = ['Familiar', 'Reviewed']
            while not data and count > 0:
                chosen_status = random.choice(statuses)
                self.cursor.execute(
                    f"SELECT id, word, category FROM words WHERE status = %s AND user_id = %s ORDER BY RANDOM() LIMIT 1;",
                    (chosen_status, user_id)
                )
                data = self.cursor.fetchall()
                count -= 1
            if chosen_status == 'Familiar':
                self.update_word_status(data[0][0], 'Reviewed')
            else:
                self.update_word_status(data[0][0], 'Memorized')

        return data[0][0], data[0][1], data[0][2], chosen_status

    def update_word_status(self, word_id, status):
        self.cursor.execute(
            "UPDATE words SET status = %s WHERE id = %s;", (status, word_id)
        )
        self.conn.commit()

    def update_settings(self, user_id, setting, choice):
        self.cursor.execute(
            f"UPDATE settings SET {setting} = %s WHERE user_id = %s;", (choice, user_id)
        )
        self.conn.commit()

    def select_all_by_word(self, word, category, user_id):
        self.cursor.execute(
            f"SELECT * FROM words WHERE word = %s AND category = %s AND user_id = %s LIMIT 1;",
            (word, category, user_id)
        )
        word_data = self.cursor.fetchall()
        if word_data:
            return word_data[0][0], word_data[0][1], word_data[0][2], word_data[0][3]
        else:
            return None

    def select_all_by_word_id(self, id):
        self.cursor.execute(
            f"SELECT * FROM words WHERE id = %s;", (id,)
        )
        word_data = self.cursor.fetchone()
        if word_data:
            return word_data
        else:
            return None

    def select_random_row(self, category, user_id):
        if category == 'All':
            self.cursor.execute(
                f"SELECT word FROM words WHERE user_id = %s ORDER BY RANDOM() LIMIT 1;", (user_id,)
            )
        else:
            self.cursor.execute(
                f"SELECT word FROM words WHERE category = %s AND user_id = %s ORDER BY RANDOM() LIMIT 1;",
                (category, user_id)
            )
        word_data = self.cursor.fetchone()
        return word_data[0] if word_data else None

    def select_count_by_category(self, category, user_id):
        self.cursor.execute(
            f"SELECT COUNT(id) FROM words WHERE category = %s AND user_id = %s;",
            (category, user_id)
        )
        count = self.cursor.fetchone()
        return count[0] if count else 0

    def select_date_delta(self, user_id):
        self.cursor.execute(
            f"SELECT modified_date FROM words WHERE user_id = %s ORDER BY modified_date DESC LIMIT 1;", (user_id,)
        )
        latest_date_row = self.cursor.fetchone()
        if latest_date_row:
            latest_date = latest_date_row[0]
            current_date = datetime.now()
            date_difference = current_date.date() - latest_date.date()
            return date_difference >= timedelta(days=1)
        else:
            return False

    def select_word_of_the_day(self, user_id):
        self.cursor.execute(
            f"SELECT word, category FROM words WHERE user_id = %s AND status <> 'New' ORDER BY RANDOM() LIMIT 1;", (user_id,)
        )
        word_of_the_day = self.cursor.fetchone()
        if word_of_the_day:
            return word_of_the_day[0], word_of_the_day[1]
        else:
            return False

    def select_setting(self, user_id, setting):
        self.cursor.execute(
            f"SELECT {setting} FROM settings WHERE user_id = %s;", (user_id,)
        )
        setting_value = self.cursor.fetchone()
        return setting_value[0] == 'enabled' if setting_value else False