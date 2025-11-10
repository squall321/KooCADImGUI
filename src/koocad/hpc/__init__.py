"""
HPC batch system integration for KooCAD.

Modules:
    - slurm: Slurm job script generation and submission
    - parameter_sweep: Design of Experiments (DoE) for parameter studies
    - apptainer: Container definition and management
    - monitoring: Job monitoring and resource tracking
    - aggregation: Result collection and analysis
"""

from __future__ import annotations

try:
    from koocad.hpc.slurm import SlurmJobGenerator
    from koocad.hpc.parameter_sweep import ParameterSweep
    from koocad.hpc.apptainer import ApptainerBuilder
    from koocad.hpc.monitoring import JobMonitor
    from koocad.hpc.aggregation import ResultAggregator
except ImportError:
    pass

__all__ = [
    "SlurmJobGenerator",
    "ParameterSweep",
    "ApptainerBuilder",
    "JobMonitor",
    "ResultAggregator",
]
