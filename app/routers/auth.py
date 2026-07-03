from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from .. import models, schemas
from ..security import verify_password, create_access_token, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES, timedelta, SECRET_KEY, ALGORITHM
from ..database import get_db

router = APIRouter(tags=["Authentication"])

# O OAuth2PasswordBearer define onde o frontend deve buscar o token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Rota para gerar o Token (O Login)
@router.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), _: None = Depends(get_db)):
    # O form_data.username conterá o email enviado pelo frontend
    try:
        user = models.User.get(models.User.email == form_data.username)
    except models.User.DoesNotExist:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha incorretos")

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha incorretos")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer", "is_superuser": user.is_superuser, "modules": user.modules}

# Rota utilitária para registrar um usuário (Apenas para você criar seu primeiro acesso)
@router.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, _: None = Depends(get_db)):
    try:
        models.User.get(models.User.email == user.email)
        raise HTTPException(status_code=400, detail="Email já registrado")
    except models.User.DoesNotExist:
        pass

    hashed_password = get_password_hash(user.password)
    db_user = models.User.create(email=user.email, hashed_password=hashed_password)
    return db_user

# Dependência que injetaremos nas rotas protegidas
def get_current_user(token: str = Depends(oauth2_scheme), _: None = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    try:
        user = models.User.get(models.User.email == email)
    except models.User.DoesNotExist:
        raise credentials_exception
        
    return user