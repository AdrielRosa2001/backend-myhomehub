"""Testes auto-contidos — setup único, limpeza entre testes."""
import os
os.environ["DATABASE_URL"] = ""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import tempfile
from unittest.mock import patch
from peewee import SqliteDatabase
from fastapi.testclient import TestClient

# ── Setup único (executado uma vez na carga do módulo) ──
tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
tmp.close()
DB_PATH = tmp.name

db = SqliteDatabase(DB_PATH)

from app.models import Transaction, User, ShoppingList, ListItem
db.create_tables([Transaction, User, ShoppingList, ListItem])

for m in [Transaction, User, ShoppingList, ListItem]:
    m._meta.database = db

def _get_db():
    db.connect(reuse_if_open=True)
    try:
        yield
    finally:
        pass

patcher1 = patch("app.database.get_db", _get_db)
patcher2 = patch("app.database.db", db)
patcher1.start()
patcher2.start()

from app.main import app
db.connect(reuse_if_open=True)
from app.security import get_password_hash


def setup_client():
    """Cria client + usuário + token. Limpa dados primeiro."""
    for m in [Transaction, User, ShoppingList, ListItem]:
        m.delete().execute()
    
    client = TestClient(app)
    User.create(email="teste@teste.com", hashed_password=get_password_hash("teste123"), is_active=True)
    resp = client.post("/api/token", data={"username": "teste@teste.com", "password": "teste123"}, headers={"Content-Type": "application/x-www-form-urlencoded"})
    token = resp.json()["access_token"]
    return client, {"Authorization": f"Bearer {token}"}


# ── Tests ──

def test_health():
    client, _ = setup_client()
    r = client.get("/api/")
    assert r.status_code == 200
    assert "MyHomeHub" in r.json()["message"]


def test_register():
    client, _ = setup_client()
    r = client.post("/api/register", json={"email": "novo@teste.com", "password": "senha123"})
    assert r.status_code == 200
    assert r.json()["email"] == "novo@teste.com"


def test_login():
    client, auth = setup_client()
    assert auth["Authorization"].startswith("Bearer ")


def test_login_invalid():
    client, _ = setup_client()
    r = client.post("/api/token", data={"username": "x@x.com", "password": "errada"}, headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert r.status_code == 401


def test_create_transaction():
    client, auth = setup_client()
    r = client.post("/api/transactions/", headers=auth, json={"description": "Teste", "amount": 100, "type": "despesa", "category": "Geral", "date": "2026-07-01"})
    assert r.status_code == 200
    assert r.json()["description"] == "Teste"


def test_list_transactions():
    client, auth = setup_client()
    r = client.get("/api/transactions/", headers=auth)
    assert r.status_code == 200


def test_create_list():
    client, auth = setup_client()
    r = client.post("/api/lists", headers=auth, json={"title": "Compras", "type": "shopping"})
    assert r.status_code == 201
    assert r.json()["title"] == "Compras"


def test_add_item():
    client, auth = setup_client()
    r1 = client.post("/api/lists", headers=auth, json={"title": "Compras", "type": "shopping"})
    lid = r1.json()["id"]
    r2 = client.post(f"/api/lists/{lid}/items", headers=auth, json={"text": "Arroz", "quantity": 1})
    assert r2.status_code == 201
    assert r2.json()["text"] == "Arroz"


def test_toggle_item():
    client, auth = setup_client()
    r1 = client.post("/api/lists", headers=auth, json={"title": "Lista", "type": "todo"})
    lid = r1.json()["id"]
    r2 = client.post(f"/api/lists/{lid}/items", headers=auth, json={"text": "Item"})
    iid = r2.json()["id"]
    r3 = client.patch(f"/api/lists/{lid}/items/{iid}", headers=auth, json={"is_completed": True})
    assert r3.status_code == 200
    assert r3.json()["is_completed"] is True


def test_archive_list():
    client, auth = setup_client()
    r1 = client.post("/api/lists", headers=auth, json={"title": "Arquivar", "type": "bullet"})
    lid = r1.json()["id"]
    r2 = client.post(f"/api/lists/{lid}/archive", headers=auth)
    assert r2.status_code == 200
    assert r2.json()["status"] == "archived"


def test_duplicate_list():
    client, auth = setup_client()
    r1 = client.post("/api/lists", headers=auth, json={"title": "Original", "type": "shopping"})
    lid = r1.json()["id"]
    client.post(f"/api/lists/{lid}/items", headers=auth, json={"text": "Item"})
    r2 = client.post(f"/api/lists/{lid}/duplicate", headers=auth)
    assert r2.status_code == 201
    assert "(cópia)" in r2.json()["title"]


def test_soft_delete():
    client, auth = setup_client()
    r1 = client.post("/api/lists", headers=auth, json={"title": "Delete", "type": "bullet"})
    lid = r1.json()["id"]
    r2 = client.delete(f"/api/lists/{lid}", headers=auth)
    assert r2.status_code == 204
