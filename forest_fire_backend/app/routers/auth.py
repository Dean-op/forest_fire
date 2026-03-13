from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import Optional

from app.database import get_session
from app.models.user import User
from app.utils.security import verify_password, create_access_token, get_password_hash
from app.config import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/api/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    username: str
    role: str

class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    confirm_password: str


async def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = session.exec(select(User).where(User.username == username)).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def validate_username(username: str) -> str:
    normalized = (username or "").strip()
    if len(normalized) < 3 or len(normalized) > 32:
        raise HTTPException(status_code=400, detail="Username length must be 3-32 characters")
    if not normalized.replace("_", "").replace("-", "").isalnum():
        raise HTTPException(status_code=400, detail="Username can only contain letters, numbers, '_' and '-'")
    return normalized


def validate_password(password: str) -> str:
    value = (password or "").strip()
    if len(value) < 6 or len(value) > 64:
        raise HTTPException(status_code=400, detail="Password length must be 6-64 characters")
    return value


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, session: Session = Depends(get_session)):
    username = validate_username(data.username)
    password = validate_password(data.password)

    if password != (data.confirm_password or "").strip():
        raise HTTPException(status_code=400, detail="Passwords do not match")

    existing = session.exec(select(User).where(User.username == username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(
        username=username,
        hashed_password=get_password_hash(password),
        role="operator",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserResponse(id=user.id, username=user.username, role=user.role)


@router.get("/me", response_model=UserResponse)
def get_user_me(current_user: User = Depends(get_current_user)):
    return UserResponse(id=current_user.id, username=current_user.username, role=current_user.role)


def require_roles(*allowed_roles: str):
    allowed = set(allowed_roles)

    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return _checker


@router.put("/password")
def update_password(pw_data: PasswordUpdate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    if not verify_password(pw_data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect old password")

    current_user.hashed_password = get_password_hash(validate_password(pw_data.new_password))
    session.add(current_user)
    session.commit()
    return {"msg": "Password updated successfully"}
