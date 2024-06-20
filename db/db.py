import logging
import sqlite3
import uuid
from datetime import datetime
import os


class BotDB:
    logger = logging.getLogger("BotDB")

    def __init__(self, db_name, sql_script=None):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
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


if __name__ == "__main__":
    db = BotDB('db_for_bot.db', 'db_creation.sql')
