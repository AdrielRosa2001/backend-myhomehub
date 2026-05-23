from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from pwdlib import PasswordHash
from dotenv import load_dotenv
from os import getenv

load_dotenv()

# Configurações de Segurança (Em produção, coloque o SECRET_KEY em variáveis de ambiente .env)
SECRET_KEY = getenv("SECRET_KEY", "b4e6dc10e48583f1cf2d162f292f5fff03bd1fb0d5dbb725aefcbe27d2be9247")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # Token válido por 7 dias

# Contexto de criptografia para gerar o hash das senhas
# O .recommended() utiliza o Argon2id automaticamente
pwd_context = PasswordHash.recommended()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt