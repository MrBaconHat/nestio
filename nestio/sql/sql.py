import sqlite3

from .compiler import Compiler


class SQL:
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.compiler = Compiler()

    async def execute(self, query):
        sql, params = self.compiler.compile(query)

        cursor = self.conn.cursor()

        cursor.execute(sql, params)

        self.conn.commit()

        return cursor.fetchall()