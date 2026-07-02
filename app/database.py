from peewee import PostgresqlDatabase, SqliteDatabase
from dotenv import load_dotenv
from os import getenv

load_dotenv()

DATABASE_URL = getenv('DATABASE_URL', '')

if DATABASE_URL:
    # PostgreSQL via DATABASE_URL (docker-compose)
    # Formato: postgresql://user:password@host:port/dbname
    db = PostgresqlDatabase(
        getenv('POSTGRES_DB', 'myhomehub'),
        user=getenv('POSTGRES_USER', 'admin'),
        password=getenv('POSTGRES_PASSWORD', 'secretpassword'),
        host=getenv('POSTGRES_HOST', 'db'),
        port=int(getenv('POSTGRES_PORT', '5432')),
    )
else:
    # Fallback: SQLite para desenvolvimento local sem Docker
    DB_NAME = getenv('DB_NAME', 'myhomehub.db')
    db = SqliteDatabase(DB_NAME, pragmas={'journal_mode': 'wal'})


def get_db():
    db.connect(reuse_if_open=True)
    try:
        yield
    finally:
        if not db.is_closed():
            db.close()