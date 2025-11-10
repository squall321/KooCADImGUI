"""
Celery tasks for file export.

Tasks:
    - export_step: Export to STEP format
    - export_stl: Export to STL format
    - export_iges: Export to IGES format
    - export_glb: Export to GLB/glTF format
    - create_archive: Create ZIP archive with multiple files
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict

try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    shared_task = lambda *args, **kwargs: lambda f: f  # type: ignore

from koocad.backend.celery_app import celery_app
from koocad.backend.models.job import JobStatus
from koocad.backend.tasks.cad_tasks import update_job_status


if CELERY_AVAILABLE:

    @celery_app.task(bind=True, name="koocad.backend.tasks.export_tasks.export_step")
    def export_step(
        self,
        job_id: int,
        shape_id: str,
        filename: str,
    ) -> Dict[str, Any]:
        """Export shape to STEP format.

        Args:
            self: Celery task instance (bound).
            job_id: Job database ID.
            shape_id: Shape identifier or cached shape reference.
            filename: Output filename.

        Returns:
            Result dictionary with file path.
        """
        try:
            asyncio.run(update_job_status(job_id, JobStatus.RUNNING, 10.0))

            # TODO: Retrieve shape from cache or regenerate
            # shape = get_cached_shape(shape_id)

            self.update_state(state="PROGRESS", meta={"progress": 50})
            asyncio.run(update_job_status(job_id, JobStatus.RUNNING, 50.0))

            # TODO: Export to STEP
            # from koocad.exporters.step import STEPExporter
            # exporter = STEPExporter()
            # file_path = exporter.export(shape, filename)

            file_path = f"exports/{filename}"

            self.update_state(state="PROGRESS", meta={"progress": 90})
            asyncio.run(update_job_status(job_id, JobStatus.RUNNING, 90.0))

            # TODO: Upload to MinIO
            # upload_to_minio(file_path)

            asyncio.run(
                update_job_status(
                    job_id,
                    JobStatus.COMPLETED,
                    100.0,
                    result_file=file_path,
                )
            )

            return {
                "status": "success",
                "file_path": file_path,
                "format": "STEP",
            }

        except Exception as e:
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

    @celery_app.task(bind=True, name="koocad.backend.tasks.export_tasks.export_stl")
    def export_stl(
        self,
        job_id: int,
        shape_id: str,
        filename: str,
        resolution: float = 0.1,
    ) -> Dict[str, Any]:
        """Export shape to STL format.

        Args:
            self: Celery task instance (bound).
            job_id: Job database ID.
            shape_id: Shape identifier.
            filename: Output filename.
            resolution: Mesh resolution.

        Returns:
            Result dictionary with file path.
        """
        try:
            asyncio.run(update_job_status(job_id, JobStatus.RUNNING, 10.0))

            self.update_state(state="PROGRESS", meta={"progress": 30})
            asyncio.run(update_job_status(job_id, JobStatus.RUNNING, 30.0))

            # TODO: Export to STL with resolution control
            # from koocad.exporters.stl import STLExporter
            # exporter = STLExporter(resolution=resolution)
            # file_path = exporter.export(shape, filename)

            file_path = f"exports/{filename}"

            self.update_state(state="PROGRESS", meta={"progress": 90})
            asyncio.run(update_job_status(job_id, JobStatus.RUNNING, 90.0))

            asyncio.run(
                update_job_status(
                    job_id,
                    JobStatus.COMPLETED,
                    100.0,
                    result_file=file_path,
                )
            )

            return {
                "status": "success",
                "file_path": file_path,
                "format": "STL",
                "resolution": resolution,
            }

        except Exception as e:
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

    @celery_app.task(bind=True, name="koocad.backend.tasks.export_tasks.export_glb")
    def export_glb(
        self,
        job_id: int,
        shape_id: str,
        filename: str,
    ) -> Dict[str, Any]:
        """Export shape to GLB/glTF format.

        Args:
            self: Celery task instance (bound).
            job_id: Job database ID.
            shape_id: Shape identifier.
            filename: Output filename.

        Returns:
            Result dictionary with file path.
        """
        try:
            asyncio.run(update_job_status(job_id, JobStatus.RUNNING, 10.0))

            self.update_state(state="PROGRESS", meta={"progress": 40})
            asyncio.run(update_job_status(job_id, JobStatus.RUNNING, 40.0))

            # TODO: Export to GLB with PBR materials
            # from koocad.exporters.gltf import GLTFExporter
            # exporter = GLTFExporter()
            # file_path = exporter.export(shape, filename)

            file_path = f"exports/{filename}"

            self.update_state(state="PROGRESS", meta={"progress": 90})
            asyncio.run(update_job_status(job_id, JobStatus.RUNNING, 90.0))

            asyncio.run(
                update_job_status(
                    job_id,
                    JobStatus.COMPLETED,
                    100.0,
                    result_file=file_path,
                )
            )

            return {
                "status": "success",
                "file_path": file_path,
                "format": "GLB",
            }

        except Exception as e:
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

    @celery_app.task(bind=True, name="koocad.backend.tasks.export_tasks.create_archive")
    def create_archive(
        self,
        job_id: int,
        file_paths: list[str],
        archive_name: str,
    ) -> Dict[str, Any]:
        """Create ZIP archive with multiple files.

        Args:
            self: Celery task instance (bound).
            job_id: Job database ID.
            file_paths: List of files to include.
            archive_name: Output archive name.

        Returns:
            Result dictionary with archive path.
        """
        try:
            import zipfile
            from pathlib import Path

            asyncio.run(update_job_status(job_id, JobStatus.RUNNING, 10.0))

            archive_path = f"exports/{archive_name}"
            Path(archive_path).parent.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for i, file_path in enumerate(file_paths):
                    progress = 10 + (80 * (i + 1) / len(file_paths))
                    self.update_state(state="PROGRESS", meta={"progress": progress})
                    asyncio.run(update_job_status(job_id, JobStatus.RUNNING, progress))

                    # Add file to archive
                    if Path(file_path).exists():
                        zf.write(file_path, Path(file_path).name)

            asyncio.run(
                update_job_status(
                    job_id,
                    JobStatus.COMPLETED,
                    100.0,
                    result_file=archive_path,
                )
            )

            return {
                "status": "success",
                "file_path": archive_path,
                "format": "ZIP",
                "file_count": len(file_paths),
            }

        except Exception as e:
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
