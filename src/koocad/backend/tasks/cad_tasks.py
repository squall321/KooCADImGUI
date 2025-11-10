"""
Celery tasks for CAD generation.

Tasks:
    - generate_cad: Generate CAD model from parameters
    - validate_parameters: Validate parameter set
    - batch_generate: Generate multiple variants
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict

try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    shared_task = lambda *args, **kwargs: lambda f: f  # type: ignore

from koocad.backend.celery_app import celery_app
from koocad.backend.config import get_settings
from koocad.backend.models.job import JobStatus

settings = get_settings()


if CELERY_AVAILABLE:

    @celery_app.task(bind=True, name="koocad.backend.tasks.cad_tasks.generate_cad")
    def generate_cad(
        self,
        job_id: int,
        parameters: Dict[str, Any],
        component_type: str,
    ) -> Dict[str, Any]:
        """Generate CAD model from parameters.

        Args:
            self: Celery task instance (bound).
            job_id: Job database ID.
            parameters: Component parameters.
            component_type: Component type (BGA, MLCC, etc.).

        Returns:
            Result dictionary with status and file path.
        """
        try:
            # Update job status to RUNNING
            asyncio.run(update_job_status(job_id, JobStatus.RUNNING, 0.0))

            # Progress update
            self.update_state(state="PROGRESS", meta={"progress": 10})
            asyncio.run(update_job_status(job_id, JobStatus.RUNNING, 10.0))

            # Generate CAD model based on component type
            if component_type == "BGA":
                result = generate_bga(parameters, self, job_id)
            elif component_type == "MLCC":
                result = generate_mlcc(parameters, self, job_id)
            elif component_type == "Resistor":
                result = generate_resistor(parameters, self, job_id)
            else:
                raise ValueError(f"Unsupported component type: {component_type}")

            # Update job status to COMPLETED
            asyncio.run(
                update_job_status(
                    job_id,
                    JobStatus.COMPLETED,
                    100.0,
                    result_file=result.get("file_path"),
                )
            )

            return result

        except Exception as e:
            # Update job status to FAILED
            error_msg = str(e)
            asyncio.run(
                update_job_status(
                    job_id,
                    JobStatus.FAILED,
                    0.0,
                    error_message=error_msg,
                )
            )
            raise


    def generate_bga(
        parameters: Dict[str, Any],
        task: Any,
        job_id: int,
    ) -> Dict[str, Any]:
        """Generate BGA package.

        Args:
            parameters: BGA parameters.
            task: Celery task for progress updates.
            job_id: Job ID.

        Returns:
            Result with file path.
        """
        try:
            from koocad.generators.bga import BGAGenerator

            # Update progress
            task.update_state(state="PROGRESS", meta={"progress": 30})
            asyncio.run(update_job_status(job_id, JobStatus.RUNNING, 30.0))

            # Create generator
            generator = BGAGenerator(
                substrate_width=parameters.get("substrate_width", 12.0),
                substrate_height=parameters.get("substrate_height", 12.0),
                substrate_thickness=parameters.get("substrate_thickness", 0.8),
                ball_rows=parameters.get("ball_rows", 15),
                ball_cols=parameters.get("ball_cols", 15),
                ball_pitch=parameters.get("ball_pitch", 0.8),
                ball_diameter=parameters.get("ball_diameter", 0.4),
            )

            # Update progress
            task.update_state(state="PROGRESS", meta={"progress": 60})
            asyncio.run(update_job_status(job_id, JobStatus.RUNNING, 60.0))

            # Generate shape
            shape = generator.generate()

            # Update progress
            task.update_state(state="PROGRESS", meta={"progress": 90})
            asyncio.run(update_job_status(job_id, JobStatus.RUNNING, 90.0))

            # Export to file (will be implemented in export_tasks)
            file_path = f"job_{job_id}_bga.step"

            # TODO: Actually export to MinIO or local storage
            # shape.export_step(file_path)

            return {
                "status": "success",
                "file_path": file_path,
                "component_type": "BGA",
                "volume": shape.volume() if hasattr(shape, "volume") else None,
            }

        except ImportError:
            # CadQuery not installed
            return {
                "status": "warning",
                "file_path": None,
                "message": "CadQuery not installed - CAD generation skipped",
            }


    def generate_mlcc(
        parameters: Dict[str, Any],
        task: Any,
        job_id: int,
    ) -> Dict[str, Any]:
        """Generate MLCC capacitor.

        Args:
            parameters: MLCC parameters.
            task: Celery task for progress updates.
            job_id: Job ID.

        Returns:
            Result with file path.
        """
        try:
            from koocad.generators.passives import MLCCGenerator

            task.update_state(state="PROGRESS", meta={"progress": 30})
            asyncio.run(update_job_status(job_id, JobStatus.RUNNING, 30.0))

            generator = MLCCGenerator(
                body_length=parameters.get("body_length", 2.0),
                body_width=parameters.get("body_width", 1.25),
                body_height=parameters.get("body_height", 1.25),
                termination_length=parameters.get("termination_length", 0.25),
            )

            task.update_state(state="PROGRESS", meta={"progress": 60})
            asyncio.run(update_job_status(job_id, JobStatus.RUNNING, 60.0))

            shape = generator.generate()

            task.update_state(state="PROGRESS", meta={"progress": 90})
            asyncio.run(update_job_status(job_id, JobStatus.RUNNING, 90.0))

            file_path = f"job_{job_id}_mlcc.step"

            return {
                "status": "success",
                "file_path": file_path,
                "component_type": "MLCC",
            }

        except ImportError:
            return {
                "status": "warning",
                "file_path": None,
                "message": "CadQuery not installed",
            }


    def generate_resistor(
        parameters: Dict[str, Any],
        task: Any,
        job_id: int,
    ) -> Dict[str, Any]:
        """Generate chip resistor.

        Args:
            parameters: Resistor parameters.
            task: Celery task for progress updates.
            job_id: Job ID.

        Returns:
            Result with file path.
        """
        try:
            from koocad.generators.passives import ChipResistorGenerator

            task.update_state(state="PROGRESS", meta={"progress": 30})
            asyncio.run(update_job_status(job_id, JobStatus.RUNNING, 30.0))

            generator = ChipResistorGenerator(
                body_length=parameters.get("body_length", 2.0),
                body_width=parameters.get("body_width", 1.25),
                body_height=parameters.get("body_height", 0.6),
                termination_length=parameters.get("termination_length", 0.25),
            )

            task.update_state(state="PROGRESS", meta={"progress": 60})
            asyncio.run(update_job_status(job_id, JobStatus.RUNNING, 60.0))

            shape = generator.generate()

            task.update_state(state="PROGRESS", meta={"progress": 90})
            asyncio.run(update_job_status(job_id, JobStatus.RUNNING, 90.0))

            file_path = f"job_{job_id}_resistor.step"

            return {
                "status": "success",
                "file_path": file_path,
                "component_type": "Resistor",
            }

        except ImportError:
            return {
                "status": "warning",
                "file_path": None,
                "message": "CadQuery not installed",
            }


async def update_job_status(
    job_id: int,
    status: JobStatus,
    progress: float,
    error_message: str | None = None,
    result_file: str | None = None,
) -> None:
    """Update job status in database.

    Args:
        job_id: Job database ID.
        status: New job status.
        progress: Progress percentage (0-100).
        error_message: Optional error message.
        result_file: Optional result file path.
    """
    try:
        from sqlalchemy import select, update
        from koocad.backend.database import AsyncSessionLocal
        from koocad.backend.models.job import Job

        async with AsyncSessionLocal() as db:
            stmt = select(Job).where(Job.id == job_id)
            result = await db.execute(stmt)
            job = result.scalar_one_or_none()

            if job:
                job.status = status
                job.progress = progress

                if status == JobStatus.RUNNING and job.started_at is None:
                    job.started_at = datetime.utcnow()
                elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                    job.completed_at = datetime.utcnow()

                if error_message:
                    job.error_message = error_message
                if result_file:
                    job.result_file = result_file

                await db.commit()

                # TODO: Send WebSocket notification (Phase 108)
                # from koocad.backend.routers.websocket import notify_job_progress
                # await notify_job_progress(
                #     job_id=job_id,
                #     user_id=job.user_id,
                #     progress=progress,
                #     status=status.value,
                #     error=error_message,
                # )

    except Exception as e:
        print(f"Error updating job status: {e}")
