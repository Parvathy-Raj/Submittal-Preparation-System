import uuid
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .models import Role, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_token(user: User) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_minutes)
    return jwt.encode({"sub": str(user.id), "role": user.role.value, "exp": expires}, settings.jwt_secret, algorithm="HS256")


def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        subject = uuid.UUID(jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])["sub"])
        user = db.scalar(select(User).where(User.id == subject, User.is_active.is_(True)))
    except (JWTError, KeyError, ValueError):
        user = None
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return user


def admin_only(user: User = Depends(current_user)) -> User:
    if user.role not in {Role.admin, Role.system_admin}:
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user


def system_admin_only(user: User = Depends(current_user)) -> User:
    if user.role != Role.system_admin:
        raise HTTPException(status_code=403, detail="System administrator access required")
    return user
