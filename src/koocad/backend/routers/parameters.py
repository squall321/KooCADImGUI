"""
Parameters router - parameter set CRUD operations.
"""

from __future__ import annotations

from typing import Any, List

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

from koocad.backend.database import get_db
from koocad.backend.dependencies import get_current_active_user
from koocad.backend.models.parameter_set import ParameterSet
from koocad.backend.models.project import Project
from koocad.backend.models.user import User
from koocad.backend.schemas.parameter_set import (
    ParameterSetCreate,
    ParameterSetResponse,
    ParameterSetUpdate,
)

if ROUTER_AVAILABLE:
    router = APIRouter()
else:
    router = None  # type: ignore


if ROUTER_AVAILABLE:

    @router.post("/", response_model=ParameterSetResponse, status_code=status.HTTP_201_CREATED)
    async def create_parameter_set(
        param_data: ParameterSetCreate,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> Any:
        """Create new parameter set.

        Args:
            param_data: Parameter set creation data.
            current_user: Current authenticated user.
            db: Database session.

        Returns:
            Created parameter set.

        Raises:
            HTTPException: If project not found or access denied.
        """
        # Verify project ownership
        stmt = select(Project).where(Project.id == param_data.project_id)
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        if project.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to add parameter sets to this project",
            )

        # Create parameter set
        db_param_set = ParameterSet(
            name=param_data.name,
            description=param_data.description,
            project_id=param_data.project_id,
            parameters=param_data.parameters,
            component_type=param_data.component_type,
        )

        db.add(db_param_set)
        await db.commit()
        await db.refresh(db_param_set)

        return db_param_set

    @router.get("/", response_model=List[ParameterSetResponse])
    async def list_parameter_sets(
        project_id: int | None = None,
        skip: int = 0,
        limit: int = 100,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> Any:
        """List parameter sets.

        Args:
            project_id: Optional project ID filter.
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            current_user: Current authenticated user.
            db: Database session.

        Returns:
            List of parameter sets.
        """
        stmt = (
            select(ParameterSet)
            .join(Project)
            .where(Project.owner_id == current_user.id)
        )

        if project_id:
            stmt = stmt.where(ParameterSet.project_id == project_id)

        stmt = stmt.offset(skip).limit(limit).order_by(ParameterSet.updated_at.desc())

        result = await db.execute(stmt)
        param_sets = result.scalars().all()

        return param_sets

    @router.get("/{param_set_id}", response_model=ParameterSetResponse)
    async def get_parameter_set(
        param_set_id: int,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> Any:
        """Get parameter set by ID.

        Args:
            param_set_id: Parameter set ID.
            current_user: Current authenticated user.
            db: Database session.

        Returns:
            Parameter set object.

        Raises:
            HTTPException: If parameter set not found or access denied.
        """
        stmt = select(ParameterSet).where(ParameterSet.id == param_set_id)
        result = await db.execute(stmt)
        param_set = result.scalar_one_or_none()

        if not param_set:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parameter set not found",
            )

        # Check ownership through project
        stmt = select(Project).where(Project.id == param_set.project_id)
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()

        if not project or project.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this parameter set",
            )

        return param_set

    @router.put("/{param_set_id}", response_model=ParameterSetResponse)
    async def update_parameter_set(
        param_set_id: int,
        param_data: ParameterSetUpdate,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> Any:
        """Update parameter set.

        Args:
            param_set_id: Parameter set ID.
            param_data: Parameter set update data.
            current_user: Current authenticated user.
            db: Database session.

        Returns:
            Updated parameter set.

        Raises:
            HTTPException: If parameter set not found or access denied.
        """
        stmt = select(ParameterSet).where(ParameterSet.id == param_set_id)
        result = await db.execute(stmt)
        param_set = result.scalar_one_or_none()

        if not param_set:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parameter set not found",
            )

        # Check ownership through project
        stmt = select(Project).where(Project.id == param_set.project_id)
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()

        if not project or project.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this parameter set",
            )

        # Update fields
        if param_data.name is not None:
            param_set.name = param_data.name
        if param_data.description is not None:
            param_set.description = param_data.description
        if param_data.parameters is not None:
            param_set.parameters = param_data.parameters
        if param_data.component_type is not None:
            param_set.component_type = param_data.component_type

        await db.commit()
        await db.refresh(param_set)

        return param_set

    @router.delete("/{param_set_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_parameter_set(
        param_set_id: int,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> None:
        """Delete parameter set.

        Args:
            param_set_id: Parameter set ID.
            current_user: Current authenticated user.
            db: Database session.

        Raises:
            HTTPException: If parameter set not found or access denied.
        """
        stmt = select(ParameterSet).where(ParameterSet.id == param_set_id)
        result = await db.execute(stmt)
        param_set = result.scalar_one_or_none()

        if not param_set:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parameter set not found",
            )

        # Check ownership through project
        stmt = select(Project).where(Project.id == param_set.project_id)
        result = await db.execute(stmt)
        project = result.scalar_one_or_none()

        if not project or project.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this parameter set",
            )

        await db.delete(param_set)
        await db.commit()
