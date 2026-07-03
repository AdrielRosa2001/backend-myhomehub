from fastapi import APIRouter, Depends, HTTPException, status, Query
from datetime import datetime
from typing import List, Optional

from .. import models, schemas
from ..database import get_db
from .auth import get_current_user

router = APIRouter(
    prefix="/lists",
    tags=["Lists"],
)

# ── Helper ─────────────────────────────────────────────────────────

def _get_list_or_404(list_id: int) -> models.ShoppingList:
    """Retorna a lista se existir, senão 404.
    Nota: futuramente implementar verificação de permissão de acesso."""
    try:
        lst = models.ShoppingList.get_by_id(list_id)
    except models.ShoppingList.DoesNotExist:
        raise HTTPException(status_code=404, detail="Lista não encontrada")
    return lst

def _get_item_or_404(item_id: int, lst: models.ShoppingList) -> models.ListItem:
    """Retorna o item se pertencer à lista, senão 404."""
    try:
        item = models.ListItem.get_by_id(item_id)
    except models.ListItem.DoesNotExist:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    if item.list_id != lst.id:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return item

# ── List Endpoints ─────────────────────────────────────────────────

@router.get("", response_model=List[schemas.ShoppingListMinimal])
def list_lists(
    type: Optional[str] = Query(None),
    status: Optional[str] = Query("active"),
    _: None = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Lista todas as listas. Filtros opcionais: type, status.
    Nota: futuramente implementar filtro por owner com permissões."""
    query = models.ShoppingList.select()
    if status:
        query = query.where(models.ShoppingList.status == status)
    if type:
        query = query.where(models.ShoppingList.type == type)
    query = query.order_by(models.ShoppingList.position, models.ShoppingList.created_at.desc())
    return list(query)


@router.post("", response_model=schemas.ShoppingListResponse, status_code=201)
def create_list(
    data: schemas.ShoppingListCreate,
    _: None = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Cria uma nova lista."""
    lst = models.ShoppingList.create(
        owner=current_user.id,
        title=data.title,
        description=data.description,
        type=data.type,
        icon=data.icon,
        position=data.position,
    )
    return lst


@router.get("/{list_id}", response_model=schemas.ShoppingListResponse)
def get_list(
    list_id: int,
    _: None = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Retorna uma lista com seus itens."""
    lst = _get_list_or_404(list_id)
    # Fetch items explicitly so they appear in the response
    lst.items = list(
        models.ListItem.select()
        .where(models.ListItem.list == lst.id)
        .order_by(models.ListItem.position, models.ListItem.created_at)
    )
    return lst


@router.patch("/{list_id}", response_model=schemas.ShoppingListResponse)
def update_list(
    list_id: int,
    data: schemas.ShoppingListUpdate,
    _: None = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Atualiza metadados de uma lista."""
    lst = _get_list_or_404(list_id)
    update_fields = data.model_dump(exclude_unset=True)
    if update_fields:
        update_fields["updated_at"] = datetime.now()
        query = models.ShoppingList.update(**update_fields).where(
            models.ShoppingList.id == lst.id
        )
        query.execute()
        lst = models.ShoppingList.get_by_id(lst.id)
    return lst


@router.delete("/{list_id}", status_code=204)
def delete_list(
    list_id: int,
    _: None = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Soft delete: marca como 'deleted' e registra deleted_at."""
    lst = _get_list_or_404(list_id)
    models.ShoppingList.update(
        status="deleted",
        deleted_at=datetime.now(),
        updated_at=datetime.now(),
    ).where(models.ShoppingList.id == lst.id).execute()
    return None


@router.post("/{list_id}/restore", response_model=schemas.ShoppingListResponse)
def restore_list(
    list_id: int,
    _: None = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Restaura uma lista da lixeira."""
    lst = _get_list_or_404(list_id)
    if lst.status != "deleted":
        raise HTTPException(status_code=400, detail="A lista não está na lixeira")
    models.ShoppingList.update(
        status="active",
        deleted_at=None,
        updated_at=datetime.now(),
    ).where(models.ShoppingList.id == lst.id).execute()
    lst = models.ShoppingList.get_by_id(lst.id)
    return lst


@router.post("/{list_id}/duplicate", response_model=schemas.ShoppingListResponse, status_code=201)
def duplicate_list(
    list_id: int,
    _: None = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Duplica uma lista. Os itens da cópia ficam desmarcados."""
    original = _get_list_or_404(list_id)

    # Duplicar a lista
    new_list = models.ShoppingList.create(
        owner=current_user.id,
        title=f"{original.title} (cópia)",
        description=original.description,
        type=original.type,
        icon=original.icon,
        status="active",
        position=original.position + 1,
    )

    # Duplicar os itens (todos is_completed=False)
    original_items = models.ListItem.select().where(
        models.ListItem.list == original.id
    )
    for item in original_items:
        models.ListItem.create(
            list=new_list.id,
            text=item.text,
            is_completed=False,
            position=item.position,
            priority=item.priority,
            due_date=item.due_date,
            quantity=item.quantity,
            unit=item.unit,
            category=item.category,
            created_by=current_user.id,
        )

    return new_list


@router.post("/{list_id}/archive", response_model=schemas.ShoppingListResponse)
def archive_list(
    list_id: int,
    _: None = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Arquiva ou desarquiva uma lista (toggle)."""
    lst = _get_list_or_404(list_id)
    new_status = "active" if lst.status == "archived" else "archived"
    models.ShoppingList.update(
        status=new_status,
        updated_at=datetime.now(),
    ).where(models.ShoppingList.id == lst.id).execute()
    lst = models.ShoppingList.get_by_id(lst.id)
    return lst


# ── Item Endpoints ─────────────────────────────────────────────────

@router.get("/{list_id}/items", response_model=List[schemas.ListItemResponse])
def list_items(
    list_id: int,
    _: None = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Lista os itens de uma lista."""
    _get_list_or_404(list_id)
    items = (
        models.ListItem.select()
        .where(models.ListItem.list == list_id)
        .order_by(models.ListItem.position, models.ListItem.created_at)
    )
    return list(items)


@router.post("/{list_id}/items", response_model=schemas.ListItemResponse, status_code=201)
def create_item(
    list_id: int,
    data: schemas.ListItemCreate,
    _: None = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Cria um item em uma lista."""
    lst = _get_list_or_404(list_id)
    item = models.ListItem.create(
        list=lst.id,
        text=data.text,
        is_completed=data.is_completed,
        position=data.position,
        priority=data.priority,
        due_date=data.due_date,
        quantity=data.quantity,
        unit=data.unit,
        category=data.category,
        price=data.price,
        created_by=current_user.id,
    )
    return item


@router.patch("/{list_id}/items/reorder", response_model=List[schemas.ListItemResponse])
def reorder_items(
    list_id: int,
    data: schemas.ListReorderRequest,
    _: None = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Reordena itens em lote (atualiza position de cada item)."""
    lst = _get_list_or_404(list_id)
    now = datetime.now()

    for pos_data in data.items:
        item = _get_item_or_404(pos_data.id, lst)
        models.ListItem.update(
            position=pos_data.position,
            updated_at=now,
        ).where(models.ListItem.id == item.id).execute()

    items = (
        models.ListItem.select()
        .where(models.ListItem.list == list_id)
        .order_by(models.ListItem.position, models.ListItem.created_at)
    )
    return list(items)


@router.patch("/{list_id}/items/{item_id}", response_model=schemas.ListItemResponse)
def update_item(
    list_id: int,
    item_id: int,
    data: schemas.ListItemUpdate,
    _: None = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Atualiza um item (inclui toggle is_completed)."""
    lst = _get_list_or_404(list_id)
    item = _get_item_or_404(item_id, lst)

    update_fields = data.model_dump(exclude_unset=True)
    if update_fields:
        update_fields["updated_at"] = datetime.now()
        query = models.ListItem.update(**update_fields).where(
            models.ListItem.id == item.id
        )
        query.execute()
        item = models.ListItem.get_by_id(item.id)
    return item


@router.delete("/{list_id}/items/{item_id}", status_code=204)
def delete_item(
    list_id: int,
    item_id: int,
    _: None = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Remove um item de uma lista."""
    lst = _get_list_or_404(list_id)
    item = _get_item_or_404(item_id, lst)
    models.ListItem.delete_by_id(item.id)
    return None
