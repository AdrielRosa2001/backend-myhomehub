from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import date, datetime
from calendar import monthrange
from .. import models, schemas
from ..database import get_db
from .auth import get_current_user

router = APIRouter(prefix="/transactions", tags=["Transactions"])

def get_transaction_or_404(transaction_id: int) -> models.Transaction:
    try:
        return models.Transaction.get_by_id(transaction_id)
    except models.Transaction.DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

@router.post("/", response_model=schemas.TransactionResponse)
def create_transaction(transaction: schemas.TransactionCreate, current_user: models.User = Depends(get_current_user), _: None = Depends(get_db)):
    db_transaction = models.Transaction.create(
        description=transaction.description,
        amount=transaction.amount,
        type=transaction.type.value,
        category=transaction.category,
        date=transaction.date or models.date.today(),
        is_paid = transaction.is_paid
    )
    return db_transaction

@router.get("/", response_model=List[schemas.TransactionResponse])
def get_transactions(
    skip: int = 0, 
    limit: int = 100,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    month: Optional[int] = Query(None, ge=1, le=12, description="Mês para filtragem rápida (1-12)"),
    year: Optional[int] = Query(None, description="Ano para filtragem rápida"),
    type: Optional[str] = None,
    category: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    search: Optional[str] = Query(None, description="Busca textual em descrição e categoria"),
    sort_by: Optional[str] = Query(None, description="Campo para ordenar (date, description, category, amount, is_paid)"),
    order: Optional[str] = Query("asc", description="Sentido da ordenação (asc ou desc)"),
    current_user: models.User = Depends(get_current_user),
    _: None = Depends(get_db)
):
    query = models.Transaction.select()

    # Filtro rápido por mês/ano (sobressai start_date/end_date se informado)
    if month is not None and year is not None:
        _, last_day = monthrange(year, month)
        query = query.where(
            (models.Transaction.date >= date(year, month, 1)) &
            (models.Transaction.date <= date(year, month, last_day))
        )
    else:
        if start_date:
            query = query.where(models.Transaction.date >= start_date)
        if end_date:
            query = query.where(models.Transaction.date <= end_date)

    if type and type != "all":
        query = query.where(models.Transaction.type == type)
    if category and category != "all":
        query = query.where(models.Transaction.category == category)
    if min_amount is not None:
        query = query.where(models.Transaction.amount >= min_amount)
    if max_amount is not None:
        query = query.where(models.Transaction.amount <= max_amount)

    # Busca textual (case-insensitive via SQLite LIKE)
    if search:
        pattern = f"%{search}%"
        query = query.where(
            (models.Transaction.description ** pattern) |
            (models.Transaction.category ** pattern)
        )

    # Ordenação
    allowed_sort_fields = {"date", "description", "category", "amount", "is_paid"}
    if sort_by and sort_by in allowed_sort_fields:
        sort_col = getattr(models.Transaction, sort_by)
        query = query.order_by(sort_col.asc() if order == "asc" else sort_col.desc())
    else:
        # Default: ordenar por data crescente (mais antiga primeiro)
        query = query.order_by(models.Transaction.date.asc())

    transactions = list(query.offset(skip).limit(limit))
    return transactions

@router.get("/{transaction_id}", response_model=schemas.TransactionResponse)
def get_transaction(transaction_id: int, current_user: models.User = Depends(get_current_user), _: None = Depends(get_db)):
    return get_transaction_or_404(transaction_id)

@router.put("/{transaction_id}", response_model=schemas.TransactionResponse)
def update_transaction(transaction_id: int, transaction: schemas.TransactionCreate, current_user: models.User = Depends(get_current_user), _: None = Depends(get_db)):
    db_transaction = get_transaction_or_404(transaction_id)
    db_transaction.description = transaction.description
    db_transaction.amount = transaction.amount
    db_transaction.type = transaction.type.value
    db_transaction.category = transaction.category
    db_transaction.date = transaction.date or db_transaction.date
    db_transaction.is_paid = transaction.is_paid
    db_transaction.save()
    return db_transaction

@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: int, current_user: models.User = Depends(get_current_user), _: None = Depends(get_db)):
    db_transaction = get_transaction_or_404(transaction_id)
    db_transaction.delete_instance()
    return None

# --- Bulk Actions ---

@router.patch("/bulk-update", response_model=schemas.BulkResponse)
def bulk_update(
    request: schemas.BulkUpdateRequest,
    current_user: models.User = Depends(get_current_user),
    _: None = Depends(get_db)
):
    if not request.ids:
        raise HTTPException(status_code=400, detail="Nenhum ID fornecido.")

    updated = 0
    for tx_id in request.ids:
        try:
            tx = models.Transaction.get_by_id(tx_id)
            if request.fields.type is not None:
                tx.type = request.fields.type.value
            if request.fields.date is not None:
                tx.date = date.fromisoformat(request.fields.date)
            if request.fields.category is not None:
                tx.category = request.fields.category
            if request.fields.is_paid is not None:
                tx.is_paid = request.fields.is_paid
            tx.save()
            updated += 1
        except models.Transaction.DoesNotExist:
            continue  # skip IDs que não existem

    return schemas.BulkResponse(
        message=f"{updated} transações atualizadas com sucesso.",
        updated_count=updated
    )

@router.post("/bulk-delete", response_model=schemas.BulkResponse)
def bulk_delete(
    request: schemas.BulkDeleteRequest,
    current_user: models.User = Depends(get_current_user),
    _: None = Depends(get_db)
):
    if not request.ids:
        raise HTTPException(status_code=400, detail="Nenhum ID fornecido.")

    deleted = models.Transaction.delete().where(
        models.Transaction.id.in_(request.ids)
    ).execute()

    return schemas.BulkResponse(
        message=f"{deleted} transações excluídas com sucesso."
    )

@router.post("/bulk-duplicate", response_model=schemas.BulkResponse, status_code=status.HTTP_201_CREATED)
def bulk_duplicate(
    request: schemas.BulkDuplicateRequest,
    current_user: models.User = Depends(get_current_user),
    _: None = Depends(get_db)
):
    if not request.ids:
        raise HTTPException(status_code=400, detail="Nenhum ID fornecido.")

    duplicated = 0
    for tx_id in request.ids:
        try:
            original = models.Transaction.get_by_id(tx_id)
            models.Transaction.create(
                description=original.description,
                amount=original.amount,
                type=request.overrides.type.value if request.overrides.type else original.type,
                date=date.fromisoformat(request.overrides.date) if request.overrides.date else original.date,
                category=request.overrides.category or original.category,
                is_paid=request.overrides.is_paid if request.overrides.is_paid is not None else original.is_paid,
            )
            duplicated += 1
        except models.Transaction.DoesNotExist:
            continue

    return schemas.BulkResponse(
        message=f"{duplicated} transações duplicadas com sucesso.",
        duplicated_count=duplicated
    )