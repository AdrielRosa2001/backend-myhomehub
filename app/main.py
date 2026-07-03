from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import db
from .models import Transaction, User, ShoppingList, ListItem
from .routers import transactions, metrics, auth, lists, users

# Inicia o banco e cria tabelas se não existirem
db.connect()
db.create_tables([Transaction, User, ShoppingList, ListItem], safe=True)
db.close()

app = FastAPI(title="MyHomeHub API", root_path="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(metrics.router)
app.include_router(lists.router)
app.include_router(users.router)

@app.get("/")
def root():
    return {"message": "MyHomeHub API operando normalmente."}
