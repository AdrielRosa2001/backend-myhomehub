from pydantic import BaseModel, ConfigDict, EmailStr, Field
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
    is_superuser: bool = False
    modules: str = '["finance","lists"]'

    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    email: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    modules: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    is_superuser: bool = False
    modules: str = '["finance","lists"]'

# ── Shopping List Schemas ──────────────────────────────────────────

class ShoppingListCreate(BaseModel):
    title: str
    description: Optional[str] = None
    type: str = "shopping"  # shopping, todo, bullet
    icon: Optional[str] = None
    position: int = 0

class ShoppingListUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    icon: Optional[str] = None
    position: Optional[int] = None

class ShoppingListResponse(BaseModel):
    id: int
    owner_id: int
    title: str
    description: Optional[str] = None
    type: str
    icon: Optional[str] = None
    status: str
    position: int
    total_price: float = 0.0
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    items: List["ListItemResponse"] = []

    model_config = ConfigDict(from_attributes=True)

class ShoppingListMinimal(BaseModel):
    """Versão reduzida da lista (sem itens) para listagens."""
    id: int
    owner_id: int
    title: str
    description: Optional[str] = None
    type: str
    icon: Optional[str] = None
    status: str
    position: int
    total_price: float = 0.0
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# ── List Item Schemas ─────────────────────────────────────────────

class ListItemCreate(BaseModel):
    text: str
    is_completed: bool = False
    position: int = 0
    priority: Optional[str] = None  # low, medium, high
    due_date: Optional[date] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None

class ListItemUpdate(BaseModel):
    text: Optional[str] = None
    is_completed: Optional[bool] = None
    position: Optional[int] = None
    priority: Optional[str] = None
    due_date: Optional[date] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None

class ListItemResponse(BaseModel):
    id: int
    list_id: int
    text: str
    is_completed: bool
    position: int
    priority: Optional[str] = None
    due_date: Optional[date] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    created_by: Optional[int] = Field(default=None, validation_alias='created_by_id', serialization_alias='created_by')
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class ItemPosition(BaseModel):
    id: int
    position: int

class ListReorderRequest(BaseModel):
    items: List[ItemPosition]

ShoppingListResponse.model_rebuild()
