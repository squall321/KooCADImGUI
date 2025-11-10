"""
FastAPI dependencies for authentication and database access.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

try:
    from fastapi import Depends, HTTPException, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from jose import JWTError, jwt
    from passlib.context import CryptContext
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    Depends = None  # type: ignore
    HTTPException = None  # type: ignore
    HTTPBearer = None  # type: ignore
    jwt = None  # type: ignore
    CryptContext = None  # type: ignore

try:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    AsyncSession = None  # type: ignore

from koocad.backend.config import get_settings
from koocad.backend.database import get_db

if DEPENDENCIES_AVAILABLE and SQLALCHEMY_AVAILABLE:
    from koocad.backend.models.user import User
    from koocad.backend.schemas.user import TokenData

settings = get_settings()

# Password hashing
if DEPENDENCIES_AVAILABLE:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash.

    Args:
        plain_password: Plain text password.
        hashed_password: Hashed password from database.

    Returns:
        True if password matches, False otherwise.
    """
    if not DEPENDENCIES_AVAILABLE:
        return False
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password.

    Args:
        password: Plain text password.

    Returns:
        Hashed password.
    """
    if not DEPENDENCIES_AVAILABLE:
        return ""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token.

    Args:
        data: Token payload data.
        expires_delta: Token expiration time delta.

    Returns:
        Encoded JWT token.
    """
    if not DEPENDENCIES_AVAILABLE:
        return ""

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),  # type: ignore
    db: AsyncSession = Depends(get_db),  # type: ignore
) -> User:
    """Get current authenticated user from JWT token.

    Args:
        credentials: HTTP bearer credentials.
        db: Database session.

    Returns:
        User object.

    Raises:
        HTTPException: If authentication fails.
    """
    if not DEPENDENCIES_AVAILABLE or not SQLALCHEMY_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dependencies not available",
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    # Get user from database
    stmt = select(User).where(User.username == token_data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),  # type: ignore
) -> User:
    """Get current active user.

    Args:
        current_user: Current user from token.

    Returns:
        Active user object.

    Raises:
        HTTPException: If user is inactive.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    return current_user
