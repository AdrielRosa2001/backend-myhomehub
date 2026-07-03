from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from .. import models, schemas
from ..database import get_db
from .auth import get_current_user
import json

router = APIRouter(prefix="/users", tags=["Users"])


def require_superuser(current_user: models.User):
    """Verifica se o usuário logado é superusuário."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem gerenciar usuários",
        )
    return current_user


@router.get("", response_model=List[schemas.UserResponse])
def list_users(
    _: None = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Lista todos os usuários (apenas admin)."""
    require_superuser(current_user)
    return list(models.User.select().order_by(models.User.id))


@router.post("", response_model=schemas.UserResponse, status_code=201)
def create_user(
    data: schemas.UserCreate,
    _: None = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Cria um novo usuário (apenas admin)."""
    require_superuser(current_user)
    from ..security import get_password_hash

    # Verifica se email já existe
    try:
        models.User.get(models.User.email == data.email)
        raise HTTPException(status_code=400, detail="Email já registrado")
    except models.User.DoesNotExist:
        pass

    user = models.User.create(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        is_active=True,
        is_superuser=False,
        modules='["finance","lists"]',
    )
    return user


@router.get("/{user_id}", response_model=schemas.UserResponse)
def get_user(
    user_id: int,
    _: None = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Detalhe de um usuário (apenas admin)."""
    require_superuser(current_user)
    try:
        return models.User.get_by_id(user_id)
    except models.User.DoesNotExist:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")


@router.patch("/{user_id}", response_model=schemas.UserResponse)
def update_user(
    user_id: int,
    data: schemas.UserUpdate,
    _: None = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Atualiza dados de um usuário (apenas admin)."""
    require_superuser(current_user)
    try:
        user = models.User.get_by_id(user_id)
    except models.User.DoesNotExist:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    update_data = data.model_dump(exclude_unset=True, exclude_none=True)
    if "email" in update_data:
        user.email = update_data["email"]
    if "is_active" in update_data:
        user.is_active = update_data["is_active"]
    if "is_superuser" in update_data:
        user.is_superuser = update_data["is_superuser"]
    if "modules" in update_data:
        # Valida se é JSON válido
        try:
            json.loads(update_data["modules"])
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="modules deve ser um JSON array válido")
        user.modules = update_data["modules"]
    user.save()
    return user


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    _: None = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Exclui um usuário (apenas admin)."""
    require_superuser(current_user)
    try:
        user = models.User.get_by_id(user_id)
    except models.User.DoesNotExist:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Não pode excluir a si mesmo
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Você não pode excluir seu próprio usuário")

    user.delete_instance()
    return None
