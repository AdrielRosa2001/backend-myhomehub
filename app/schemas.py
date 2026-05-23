from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime, date
from enum import Enum
from typing import List, Optional

class TransactionType(str, Enum):
    receita = "receita"
    despesa = "despesa"

class TransactionBase(BaseModel):
    description: str
    amount: float
    type: TransactionType
    category: str
    date: date

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: int
    
    # Permite que o Pydantic leia diretamente dos atributos do modelo Peewee
    model_config = ConfigDict(from_attributes=True)

class SummaryResponse(BaseModel):
    total_receitas: float
    total_despesas: float
    saldo: float

class ChartDataPoint(BaseModel):
    date: date
    receitas: float
    despesas: float

class ChartDataResponse(BaseModel):
    data: List[ChartDataPoint]

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str