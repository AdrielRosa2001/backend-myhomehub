from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import date
from .. import models, schemas
from ..database import get_db
from .auth import get_current_user # Importe a função

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
    type: Optional[str] = None,
    category: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    current_user: models.User = Depends(get_current_user),
    _: None = Depends(get_db)
):
    query = models.Transaction.select()

    # Aplicando os filtros dinamicamente
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