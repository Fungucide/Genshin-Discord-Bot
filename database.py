import datetime
import sqlite3


class Database:
    db: sqlite3.Connection

    def __init__(self, db_file):
        try:
            self.db = sqlite3.connect(db_file)
        except sqlite3.Error as e:
            print(e)

    def make_emoji_table(self):
        cursor = self.db.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS emoji(
            id integer PRIMARY  KEY,
            name text NOT NULL UNIQUE,
            category text NOT NULL,
            url text NOT NULL,
            discord_id text,
            last_update text NOT NULL
        ) 
        """)

    def add_emoji(self, name: str, category: str, url: str, overwrite: bool = False) -> bool:
        if self.get_emoji(name):
            if overwrite:
                self.delete_emoji(name)
            else:
                return False
        cursor = self.db.cursor()
        cursor.execute("INSERT INTO emoji(name,category,url,last_update) VALUES(?,?,?,?)",
                       [name, category, url, datetime.datetime.now()])
        self.db.commit()
        return True

    def delete_emoji(self, name: str):
        cursor = self.db.cursor()
        cursor.execute("DELETE FROM emoji WHERE name=?", [name])
        self.db.commit()
        return cursor.rowcount

    def get_emoji(self, name: str):
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM emoji WHERE name=?", [name])
        res = cursor.fetchall()
        if len(res) == 0:
            return None
        if len(res) != 1:
            raise Exception(f"Expected 1 result got {len(res)} for query {name}")
            return None
        return dict((cursor.description[i][0], value) for i, value in enumerate(res[0]))

    def get_category_emoji(self, category: str):
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM emoji WHERE category=?", [category])
        r = [dict((cursor.description[i][0], value) for i, value in enumerate(row)) for row in cursor.fetchall()]
        return r

    def set_emoji_discord_id(self, name: str, discord_id: str):
        cursor = self.db.cursor()
        cursor.execute("UPDATE emoji SET discord_id=? WHERE name=?", [discord_id, name])
        self.db.commit()
        if cursor.rowcount != 1:
            raise Exception(f"Error occured when trying to update {name}")
