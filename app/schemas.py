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
    is_paid: bool = False

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

class MonthlyChartPoint(BaseModel):
    month: str  # "Jan", "Fev", etc.
    receitas: float
    despesas: float

class AnnualChartResponse(BaseModel):
    year: int
    data: List[MonthlyChartPoint]

class BulkUpdateFields(BaseModel):
    type: Optional[TransactionType] = None
    date: Optional[str] = None  # Aceita string ISO yyyy-mm-dd
    category: Optional[str] = None
    is_paid: Optional[bool] = None

class BulkUpdateRequest(BaseModel):
    ids: List[int]
    fields: BulkUpdateFields

class BulkDeleteRequest(BaseModel):
    ids: List[int]

class BulkDuplicateRequest(BaseModel):
    ids: List[int]
    overrides: BulkUpdateFields

class BulkResponse(BaseModel):
    message: str
    updated_count: Optional[int] = None
    duplicated_count: Optional[int] = None

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