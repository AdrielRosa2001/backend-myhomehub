from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import db
from .models import Transaction
from .routers import transactions, metrics
from .models import Transaction, User # Importe o User
from .routers import transactions, metrics, auth # Importe o auth

# Inicia o banco e cria tabelas se não existirem
db.connect()
db.create_tables([Transaction, User], safe=True) # Crie a tabela User
db.close()

app = FastAPI(title="MyFinance API")

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

@app.get("/")
def root():
    return {"message": "MyFinance API operando normalmente."}