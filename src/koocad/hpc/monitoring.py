"""
Job monitoring and status tracking.

Features:
- Query job status from Slurm
- Resource utilization tracking
- Job statistics and reporting
- Email notifications
"""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import json


class JobMonitor:
    """Slurm job monitoring and tracking."""

    def __init__(self):
        """Initialize job monitor."""
        self.jobs: Dict[int, Dict[str, Any]] = {}

    def query_job(
        self,
        job_id: int,
    ) -> Optional[Dict[str, Any]]:
        """Query job status from Slurm.

        Args:
            job_id: Slurm job ID.

        Returns:
            Job information dictionary, or None if query fails.
        """
        try:
            cmd = [
                "scontrol",
                "show",
                "job",
                str(job_id),
                "--oneline",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            # Parse scontrol output
            job_info = self._parse_scontrol_output(result.stdout)
            self.jobs[job_id] = job_info
            return job_info

        except subprocess.CalledProcessError:
            return None
        except FileNotFoundError:
            print("Error: scontrol command not found")
            return None

    def query_jobs(
        self,
        user: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Query all jobs for user.

        Args:
            user: Username (default: current user).

        Returns:
            List of job information dictionaries.
        """
        try:
            cmd = ["squeue", "--format=%A|%T|%j|%u|%M|%l|%D|%C", "--noheader"]

            if user:
                cmd.extend(["--user", user])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            jobs = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("|")
                if len(parts) >= 8:
                    job_info = {
                        "job_id": int(parts[0]),
                        "state": parts[1],
                        "name": parts[2],
                        "user": parts[3],
                        "time": parts[4],
                        "time_limit": parts[5],
                        "nodes": int(parts[6]),
                        "cpus": int(parts[7]),
                    }
                    jobs.append(job_info)
                    self.jobs[job_info["job_id"]] = job_info

            return jobs

        except subprocess.CalledProcessError as e:
            print(f"Query failed: {e.stderr}")
            return []
        except FileNotFoundError:
            print("Error: squeue command not found")
            return []

    def get_job_efficiency(
        self,
        job_id: int,
    ) -> Optional[Dict[str, float]]:
        """Get job efficiency metrics.

        Args:
            job_id: Slurm job ID.

        Returns:
            Efficiency metrics dictionary.
        """
        try:
            cmd = [
                "seff",
                str(job_id),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            # Parse seff output
            efficiency = self._parse_seff_output(result.stdout)
            return efficiency

        except subprocess.CalledProcessError:
            return None
        except FileNotFoundError:
            print("Error: seff command not found")
            return None

    def cancel_job(
        self,
        job_id: int,
    ) -> bool:
        """Cancel Slurm job.

        Args:
            job_id: Job ID to cancel.

        Returns:
            True if successful, False otherwise.
        """
        try:
            cmd = ["scancel", str(job_id)]

            subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            print(f"Cancelled job {job_id}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"Cancel failed: {e.stderr}")
            return False
        except FileNotFoundError:
            print("Error: scancel command not found")
            return False

    def wait_for_completion(
        self,
        job_ids: List[int],
        poll_interval: int = 30,
        timeout: Optional[int] = None,
    ) -> Dict[int, str]:
        """Wait for jobs to complete.

        Args:
            job_ids: List of job IDs to wait for.
            poll_interval: Polling interval in seconds.
            timeout: Maximum wait time in seconds.

        Returns:
            Dictionary mapping job ID to final state.
        """
        import time

        start_time = time.time()
        job_states = {}

        while job_ids:
            # Check if timeout exceeded
            if timeout and (time.time() - start_time) > timeout:
                print("Timeout exceeded")
                break

            # Query job status
            remaining_jobs = []
            for job_id in job_ids:
                job_info = self.query_job(job_id)

                if job_info is None:
                    # Job not found (likely completed)
                    job_states[job_id] = "COMPLETED"
                else:
                    state = job_info.get("JobState", "UNKNOWN")

                    if state in ["COMPLETED", "FAILED", "CANCELLED", "TIMEOUT"]:
                        job_states[job_id] = state
                    else:
                        remaining_jobs.append(job_id)

            job_ids = remaining_jobs

            if job_ids:
                time.sleep(poll_interval)

        return job_states

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics for tracked jobs.

        Returns:
            Statistics dictionary.
        """
        if not self.jobs:
            return {}

        states = {}
        total_cpus = 0
        total_nodes = 0

        for job_info in self.jobs.values():
            state = job_info.get("state", "UNKNOWN")
            states[state] = states.get(state, 0) + 1
            total_cpus += job_info.get("cpus", 0)
            total_nodes += job_info.get("nodes", 0)

        return {
            "total_jobs": len(self.jobs),
            "states": states,
            "total_cpus": total_cpus,
            "total_nodes": total_nodes,
        }

    def export_report(
        self,
        filepath: str | Path,
    ) -> Path:
        """Export monitoring report to JSON.

        Args:
            filepath: Output file path.

        Returns:
            Path to exported file.
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        report = {
            "timestamp": datetime.now().isoformat(),
            "statistics": self.get_statistics(),
            "jobs": self.jobs,
        }

        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)

        return filepath

    def _parse_scontrol_output(
        self,
        output: str,
    ) -> Dict[str, Any]:
        """Parse scontrol output.

        Args:
            output: scontrol output text.

        Returns:
            Parsed job information.
        """
        job_info = {}

        for item in output.split():
            if "=" in item:
                key, value = item.split("=", 1)
                job_info[key] = value

        return job_info

    def _parse_seff_output(
        self,
        output: str,
    ) -> Dict[str, float]:
        """Parse seff output.

        Args:
            output: seff output text.

        Returns:
            Parsed efficiency metrics.
        """
        efficiency = {}

        for line in output.split("\n"):
            if "CPU Efficiency" in line:
                # Extract percentage
                parts = line.split()
                for part in parts:
                    if "%" in part:
                        efficiency["cpu_efficiency"] = float(part.rstrip("%"))

            elif "Memory Efficiency" in line:
                parts = line.split()
                for part in parts:
                    if "%" in part:
                        efficiency["memory_efficiency"] = float(part.rstrip("%"))

        return efficiency
