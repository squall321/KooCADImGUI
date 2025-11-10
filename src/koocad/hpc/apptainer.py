"""
Apptainer (Singularity) container builder.

Creates container definition files (.def) for HPC environments.

Features:
- Base image selection
- Package installation
- Environment variables
- Bind mount points
- GPU support
- MPI integration
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional


class ApptainerBuilder:
    """Apptainer container definition builder."""

    def __init__(
        self,
        base_image: str = "docker://ubuntu:22.04",
    ):
        """Initialize Apptainer builder.

        Args:
            base_image: Base container image.
        """
        self.base_image = base_image
        self.packages: List[str] = []
        self.python_packages: List[str] = []
        self.files: List[tuple[str, str]] = []
        self.environment: Dict[str, str] = {}
        self.runscript: List[str] = []
        self.post_commands: List[str] = []
        self.labels: Dict[str, str] = {}

    def add_package(self, *packages: str) -> None:
        """Add system packages to install.

        Args:
            *packages: Package names.
        """
        self.packages.extend(packages)

    def add_python_package(self, *packages: str) -> None:
        """Add Python packages to install.

        Args:
            *packages: Python package names.
        """
        self.python_packages.extend(packages)

    def add_file(
        self,
        source: str,
        dest: str,
    ) -> None:
        """Add file to copy into container.

        Args:
            source: Source file path (on host).
            dest: Destination path (in container).
        """
        self.files.append((source, dest))

    def set_environment(
        self,
        key: str,
        value: str,
    ) -> None:
        """Set environment variable.

        Args:
            key: Variable name.
            value: Variable value.
        """
        self.environment[key] = value

    def add_runscript_line(self, command: str) -> None:
        """Add line to runscript.

        Args:
            command: Shell command.
        """
        self.runscript.append(command)

    def add_post_command(self, command: str) -> None:
        """Add command to post-installation section.

        Args:
            command: Shell command.
        """
        self.post_commands.append(command)

    def set_label(self, key: str, value: str) -> None:
        """Set container label.

        Args:
            key: Label key.
            value: Label value.
        """
        self.labels[key] = value

    def generate_definition(
        self,
        filepath: str | Path,
    ) -> Path:
        """Generate Apptainer definition file.

        Args:
            filepath: Output .def file path.

        Returns:
            Path to generated definition file.
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Ensure .def extension
        if filepath.suffix != ".def":
            filepath = filepath.with_suffix(".def")

        with open(filepath, "w") as f:
            # Bootstrap section
            f.write("Bootstrap: docker\n")
            f.write(f"From: {self.base_image.replace('docker://', '')}\n")
            f.write("\n")

            # Labels section
            if self.labels:
                f.write("%labels\n")
                for key, value in self.labels.items():
                    f.write(f"    {key} {value}\n")
                f.write("\n")

            # Files section
            if self.files:
                f.write("%files\n")
                for source, dest in self.files:
                    f.write(f"    {source} {dest}\n")
                f.write("\n")

            # Environment section
            if self.environment:
                f.write("%environment\n")
                for key, value in self.environment.items():
                    f.write(f"    export {key}={value}\n")
                f.write("\n")

            # Post-installation section
            f.write("%post\n")
            f.write("    # Update package lists\n")
            f.write("    apt-get update -y\n")
            f.write("\n")

            # Install system packages
            if self.packages:
                f.write("    # Install system packages\n")
                pkg_list = " ".join(self.packages)
                f.write(f"    apt-get install -y {pkg_list}\n")
                f.write("\n")

            # Install Python packages
            if self.python_packages:
                f.write("    # Install Python packages\n")
                pkg_list = " ".join(self.python_packages)
                f.write(f"    pip3 install --no-cache-dir {pkg_list}\n")
                f.write("\n")

            # Custom post commands
            if self.post_commands:
                f.write("    # Custom installation commands\n")
                for cmd in self.post_commands:
                    f.write(f"    {cmd}\n")
                f.write("\n")

            # Clean up
            f.write("    # Clean up\n")
            f.write("    apt-get clean\n")
            f.write("    rm -rf /var/lib/apt/lists/*\n")
            f.write("\n")

            # Runscript section
            if self.runscript:
                f.write("%runscript\n")
                for cmd in self.runscript:
                    f.write(f"    {cmd}\n")
                f.write("\n")

            # Help section
            f.write("%help\n")
            f.write("    This is a KooCAD container for parametric CAD generation.\n")
            f.write("    \n")
            f.write("    Usage:\n")
            f.write("        apptainer run container.sif [args]\n")
            f.write("        apptainer exec container.sif python script.py\n")
            f.write("\n")

        return filepath

    def build(
        self,
        def_file: str | Path,
        output_image: str | Path,
        fakeroot: bool = False,
        force: bool = False,
    ) -> Optional[Path]:
        """Build Apptainer container image.

        Args:
            def_file: Definition file path.
            output_image: Output .sif file path.
            fakeroot: Use fakeroot for rootless build.
            force: Force overwrite of existing image.

        Returns:
            Path to built image, or None if build fails.
        """
        import subprocess

        def_file = Path(def_file)
        output_image = Path(output_image)

        if not def_file.exists():
            raise FileNotFoundError(f"Definition file not found: {def_file}")

        # Ensure .sif extension
        if output_image.suffix != ".sif":
            output_image = output_image.with_suffix(".sif")

        # Build command
        cmd = ["apptainer", "build"]

        if fakeroot:
            cmd.append("--fakeroot")
        if force:
            cmd.append("--force")

        cmd.extend([str(output_image), str(def_file)])

        print(f"Building container: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            print("Build successful!")
            print(result.stdout)
            return output_image

        except subprocess.CalledProcessError as e:
            print(f"Build failed: {e.stderr}")
            return None
        except FileNotFoundError:
            print("Error: apptainer command not found. Is Apptainer installed?")
            return None

    @staticmethod
    def create_koocad_container() -> "ApptainerBuilder":
        """Create pre-configured KooCAD container.

        Returns:
            Configured ApptainerBuilder.
        """
        builder = ApptainerBuilder(base_image="docker://python:3.11-slim")

        # System packages
        builder.add_package(
            "build-essential",
            "git",
            "libgl1-mesa-glx",
            "libglib2.0-0",
            "libsm6",
            "libxext6",
            "libxrender-dev",
        )

        # Python packages
        builder.add_python_package(
            "cadquery",
            "fastapi",
            "uvicorn",
            "celery",
            "redis",
            "sqlalchemy",
            "asyncpg",
        )

        # Environment
        builder.set_environment("PYTHONUNBUFFERED", "1")
        builder.set_environment("KOOCAD_VERSION", "1.0.0")

        # Labels
        builder.set_label("Author", "KooCAD Project")
        builder.set_label("Version", "1.0.0")
        builder.set_label("Description", "Parametric CAD generation system")

        # Runscript
        builder.add_runscript_line("#!/bin/bash")
        builder.add_runscript_line('echo "KooCAD Container"')
        builder.add_runscript_line('exec python "$@"')

        return builder
