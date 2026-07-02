"""
Script de migração: SQLite -> PostgreSQL

Uso:
  1. Suba os containers com PostgreSQL: docker compose up -d --build
  2. Copie o SQLite antigo para o container: docker cp data/myhomehub.db myhomehub-backend:/app/myhomehub.db
  3. Execute: docker compose exec backend python migrate_data.py
"""

from peewee import SqliteDatabase
from app.database import db as pg_db
from app.models import Transaction, User, BaseModel

# 1. Conectar ao SQLite antigo
SQLITE_PATH = "myhomehub.db"
sqlite_db = SqliteDatabase(SQLITE_PATH)

# Lista dos modelos na ordem correta de dependência
models = [User, Transaction]


def run_migration():
    print(f"Iniciando migração de {SQLITE_PATH} -> PostgreSQL...")

    # 2. Criar tabelas no PostgreSQL
    pg_db.connect()
    pg_db.create_tables(models, safe=True)
    print("Tabelas criadas no PostgreSQL.")

    # 3. Migrar cada modelo
    for model in models:
        table_name = model._meta.table_name
        print(f"\nMigrando tabela {table_name}...")

        # Aponta modelo para o SQLite para ler
        model._meta.database = sqlite_db
        sqlite_db.connect(reuse_if_open=True)
        records = list(model.select().dicts())
        sqlite_db.close()

        print(f"  → {len(records)} registros lidos do SQLite")

        # Aponta modelo para o PostgreSQL para escrever
        model._meta.database = pg_db

        if records:
            with pg_db.atomic():
                for i in range(0, len(records), 100):
                    batch = records[i : i + 100]
                    model.insert_many(batch).execute()
            print(f"  → {len(records)} registros inseridos no PostgreSQL")
        else:
            print(f"  → Nenhum registro para migrar.")

    pg_db.close()
    print("\n✅ Migração concluída com sucesso!")
    print("Remova o arquivo myhomehub.db após confirmar que os dados estão OK.")


if __name__ == "__main__":
    run_migration()
