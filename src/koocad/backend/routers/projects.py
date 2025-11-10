"""
Projects router - project CRUD operations.
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
from koocad.backend.models.project import Project
from koocad.backend.models.user import User
from koocad.backend.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

if ROUTER_AVAILABLE:
    router = APIRouter()
else:
    router = None  # type: ignore


if ROUTER_AVAILABLE:

    @router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
    async def create_project(
        project_data: ProjectCreate,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> Any:
        """Create new project.

        Args:
            project_data: Project creation data.
            current_user: Current authenticated user.
            db: Database session.

        Returns:
            Created project.
        """
        db_project = Project(
            name=project_data.name,
            description=project_data.description,
            owner_id=current_user.id,
        )

        db.add(db_project)
        await db.commit()
        await db.refresh(db_project)

        return db_project

    @router.get("/", response_model=List[ProjectResponse])
    async def list_projects(
        skip: int = 0,
        limit: int = 100,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> Any:
        """List user's projects.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            current_user: Current authenticated user.
            db: Database session.

        Returns:
            List of projects.
        """
        stmt = (
            select(Project)
            .where(Project.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
            .order_by(Project.updated_at.desc())
        )
        result = await db.execute(stmt)
        projects = result.scalars().all()

        return projects

    @router.get("/{project_id}", response_model=ProjectResponse)
    async def get_project(
        project_id: int,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> Any:
        """Get project by ID.

        Args:
            project_id: Project ID.
            current_user: Current authenticated user.
            db: Database session.

        Returns:
            Project object.

        Raises:
            HTTPException: If project not found or access denied.
        """
        stmt = select(Project).where(Project.id == project_id)
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
                detail="Not authorized to access this project",
            )

        return project

    @router.put("/{project_id}", response_model=ProjectResponse)
    async def update_project(
        project_id: int,
        project_data: ProjectUpdate,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> Any:
        """Update project.

        Args:
            project_id: Project ID.
            project_data: Project update data.
            current_user: Current authenticated user.
            db: Database session.

        Returns:
            Updated project.

        Raises:
            HTTPException: If project not found or access denied.
        """
        stmt = select(Project).where(Project.id == project_id)
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
                detail="Not authorized to update this project",
            )

        # Update fields
        if project_data.name is not None:
            project.name = project_data.name
        if project_data.description is not None:
            project.description = project_data.description

        await db.commit()
        await db.refresh(project)

        return project

    @router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_project(
        project_id: int,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> None:
        """Delete project.

        Args:
            project_id: Project ID.
            current_user: Current authenticated user.
            db: Database session.

        Raises:
            HTTPException: If project not found or access denied.
        """
        stmt = select(Project).where(Project.id == project_id)
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
                detail="Not authorized to delete this project",
            )

        await db.delete(project)
        await db.commit()
