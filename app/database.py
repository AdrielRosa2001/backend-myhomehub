from peewee import SqliteDatabase
from dotenv import load_dotenv
from os import getenv

load_dotenv()
DB_NAME = getenv('DB_NAME', "testdb.db")
# O modo WAL (Write-Ahead Logging) melhora a concorrência no SQLite
db = SqliteDatabase(DB_NAME, pragmas={'journal_mode': 'wal'})


def get_db():
    db.connect(reuse_if_open=True)
    try:
        yield
    finally:
        if not db.is_closed():
            db.close()