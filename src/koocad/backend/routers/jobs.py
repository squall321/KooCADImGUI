"""
Jobs router - CAD generation and export job management.
"""

from __future__ import annotations

from typing import Any, List
import uuid

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
from koocad.backend.models.job import Job, JobStatus
from koocad.backend.models.user import User
from koocad.backend.schemas.job import JobCreate, JobResponse

if ROUTER_AVAILABLE:
    router = APIRouter()
else:
    router = None  # type: ignore


if ROUTER_AVAILABLE:

    @router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
    async def create_job(
        job_data: JobCreate,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> Any:
        """Create and submit new job.

        Args:
            job_data: Job creation data.
            current_user: Current authenticated user.
            db: Database session.

        Returns:
            Created job with task ID.
        """
        # Generate task ID
        task_id = f"task-{uuid.uuid4().hex[:16]}"

        # Create job record
        db_job = Job(
            task_id=task_id,
            job_type=job_data.job_type,
            status=JobStatus.PENDING,
            user_id=current_user.id,
            project_id=job_data.project_id,
            parameter_set_id=job_data.parameter_set_id,
            parameters=job_data.parameters,
        )

        db.add(db_job)
        await db.commit()
        await db.refresh(db_job)

        # Submit to Celery task queue
        try:
            from koocad.backend.tasks.cad_tasks import generate_cad
            from koocad.backend.tasks.export_tasks import export_step, export_stl, export_glb
            from koocad.backend.models.job import JobType

            # Dispatch based on job type
            if job_data.job_type == JobType.CAD_GENERATION:
                component_type = job_data.parameters.get("component_type", "BGA")
                generate_cad.delay(db_job.id, job_data.parameters, component_type)
            elif job_data.job_type == JobType.EXPORT_STEP:
                shape_id = job_data.parameters.get("shape_id")
                filename = job_data.parameters.get("filename", f"export_{db_job.id}.step")
                export_step.delay(db_job.id, shape_id, filename)
            elif job_data.job_type == JobType.EXPORT_STL:
                shape_id = job_data.parameters.get("shape_id")
                filename = job_data.parameters.get("filename", f"export_{db_job.id}.stl")
                resolution = job_data.parameters.get("resolution", 0.1)
                export_stl.delay(db_job.id, shape_id, filename, resolution)
            elif job_data.job_type == JobType.EXPORT_GLB:
                shape_id = job_data.parameters.get("shape_id")
                filename = job_data.parameters.get("filename", f"export_{db_job.id}.glb")
                export_glb.delay(db_job.id, shape_id, filename)
        except ImportError:
            # Celery not available - job stays in PENDING state
            pass

        return db_job

    @router.get("/", response_model=List[JobResponse])
    async def list_jobs(
        skip: int = 0,
        limit: int = 100,
        status_filter: JobStatus | None = None,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> Any:
        """List user's jobs.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            status_filter: Optional status filter.
            current_user: Current authenticated user.
            db: Database session.

        Returns:
            List of jobs.
        """
        stmt = select(Job).where(Job.user_id == current_user.id)

        if status_filter:
            stmt = stmt.where(Job.status == status_filter)

        stmt = stmt.offset(skip).limit(limit).order_by(Job.created_at.desc())

        result = await db.execute(stmt)
        jobs = result.scalars().all()

        return jobs

    @router.get("/{job_id}", response_model=JobResponse)
    async def get_job(
        job_id: int,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> Any:
        """Get job by ID.

        Args:
            job_id: Job ID.
            current_user: Current authenticated user.
            db: Database session.

        Returns:
            Job object.

        Raises:
            HTTPException: If job not found or access denied.
        """
        stmt = select(Job).where(Job.id == job_id)
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found",
            )

        if job.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this job",
            )

        return job

    @router.post("/{job_id}/cancel", response_model=JobResponse)
    async def cancel_job(
        job_id: int,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> Any:
        """Cancel a pending or running job.

        Args:
            job_id: Job ID.
            current_user: Current authenticated user.
            db: Database session.

        Returns:
            Updated job object.

        Raises:
            HTTPException: If job not found, access denied, or cannot be cancelled.
        """
        stmt = select(Job).where(Job.id == job_id)
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found",
            )

        if job.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to cancel this job",
            )

        if job.status not in [JobStatus.PENDING, JobStatus.RUNNING]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel job with status {job.status}",
            )

        # TODO: Revoke Celery task (Phase 110)
        # from celery import current_app
        # current_app.control.revoke(job.task_id, terminate=True)

        job.status = JobStatus.CANCELLED
        await db.commit()
        await db.refresh(job)

        return job

    @router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_job(
        job_id: int,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> None:
        """Delete job record.

        Args:
            job_id: Job ID.
            current_user: Current authenticated user.
            db: Database session.

        Raises:
            HTTPException: If job not found or access denied.
        """
        stmt = select(Job).where(Job.id == job_id)
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found",
            )

        if job.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this job",
            )

        await db.delete(job)
        await db.commit()
