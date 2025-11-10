"""
Authentication router - login, register, token management.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

try:
    from fastapi import APIRouter, Depends, HTTPException, status
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
    ROUTER_AVAILABLE = True
except ImportError:
    ROUTER_AVAILABLE = False
    APIRouter = None  # type: ignore
    Depends = None  # type: ignore
    HTTPException = None  # type: ignore
    AsyncSession = None  # type: ignore

from koocad.backend.config import get_settings
from koocad.backend.database import get_db
from koocad.backend.dependencies import (
    create_access_token,
    get_current_active_user,
    get_password_hash,
    verify_password,
)
from koocad.backend.models.user import User, UserRole
from koocad.backend.schemas.user import Token, UserCreate, UserLogin, UserResponse

settings = get_settings()

if ROUTER_AVAILABLE:
    router = APIRouter()
else:
    router = None  # type: ignore


if ROUTER_AVAILABLE:

    @router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
    async def register(
        user_data: UserCreate,
        db: AsyncSession = Depends(get_db),
    ) -> Any:
        """Register new user.

        Args:
            user_data: User registration data.
            db: Database session.

        Returns:
            Created user object.

        Raises:
            HTTPException: If username or email already exists.
        """
        # Check if username exists
        stmt = select(User).where(User.username == user_data.username)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )

        # Check if email exists
        stmt = select(User).where(User.email == user_data.email)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Create new user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            role=UserRole.USER,
        )

        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        return db_user

    @router.post("/login", response_model=Token)
    async def login(
        credentials: UserLogin,
        db: AsyncSession = Depends(get_db),
    ) -> Any:
        """Login and get access token.

        Args:
            credentials: Login credentials.
            db: Database session.

        Returns:
            Access token.

        Raises:
            HTTPException: If credentials are invalid.
        """
        # Get user from database
        stmt = select(User).where(User.username == credentials.username)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user",
            )

        # Create access token
        access_token_expires = timedelta(minutes=settings.jwt_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id},
            expires_delta=access_token_expires,
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.jwt_expire_minutes * 60,
        }

    @router.get("/me", response_model=UserResponse)
    async def get_current_user_info(
        current_user: User = Depends(get_current_active_user),
    ) -> Any:
        """Get current user information.

        Args:
            current_user: Current authenticated user.

        Returns:
            User information.
        """
        return current_user
