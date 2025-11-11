import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import select

from .db import get_session
from .models import User


SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

router = APIRouter()


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme), session=Depends(get_session)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = session.exec(select(User).where(User.email == email)).first()
    if user is None:
        raise credentials_exception
    return user


@router.post("/register", status_code=201, response_model=Token)
def register(form_data: OAuth2PasswordRequestForm = Depends(), session=Depends(get_session)):
    """Register a new user. Uses form fields `username` and `password` from OAuth2 form spec."""
    email = form_data.username
    password = form_data.password

    existing = session.exec(select(User).where(User.email == email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(email=email, hashed_password=get_password_hash(password))
    session.add(user)
    session.commit()
    session.refresh(user)

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), session=Depends(get_session)):
    user = session.exec(select(User).where(User.email == form_data.username)).first()
    if not user or not user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    return {"email": current_user.email, "name": current_user.name, "role": current_user.role}
