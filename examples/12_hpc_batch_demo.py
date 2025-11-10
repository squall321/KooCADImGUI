#!/usr/bin/env python
"""
KooCAD HPC Batch System Demo.

This example demonstrates the complete HPC workflow:
- Slurm job script generation
- Parameter sweep (Cartesian, Random, Sobol)
- Apptainer container building
- Job submission and monitoring
- Result aggregation and analysis

Phase 136-145 Complete (FINAL):
- Slurm job script generator
- Parameter sweep (DoE)
- Apptainer container builder
- Job monitoring and tracking
- Result aggregation with statistics

This completes the entire 145-phase KooCAD project! 🎉

Requirements:
    pip install scipy matplotlib  # For advanced sampling and plotting

Optional (for actual HPC submission):
    - Slurm workload manager
    - Apptainer/Singularity

Usage:
    python examples/12_hpc_batch_demo.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def demo_slurm_job():
    """Demonstrate Slurm job script generation."""
    print("=" * 70)
    print("Slurm Job Script Generation")
    print("=" * 70)

    from koocad.hpc.slurm import SlurmJobGenerator

    # Create job generator
    print("\n1. Creating Slurm job script...")
    job = SlurmJobGenerator(
        job_name="koocad_cad_gen",
        partition="compute",
        nodes=1,
        ntasks=1,
        cpus_per_task=8,
        mem_per_cpu="4G",
        time="02:00:00",
    )

    # Configure job
    job.set_account("research_project")
    job.set_qos("normal")
    job.set_email_notification("user@example.com", "END,FAIL")

    # Add modules and commands
    job.add_module("python/3.11")
    job.add_module("gcc/11.2")
    job.set_environment("OMP_NUM_THREADS", "8")

    job.add_command("echo 'Starting CAD generation...'")
    job.add_command("python generate_cad.py --config config.json")
    job.add_command("echo 'CAD generation complete!'")

    # Generate script
    output_dir = Path("output/hpc")
    output_dir.mkdir(parents=True, exist_ok=True)

    script_path = job.generate(output_dir / "job_single.sh")
    print(f"   ✓ Generated: {script_path}")

    # Show script content
    print("\n2. Script content:")
    with open(script_path, "r") as f:
        print(f.read())


def demo_parameter_sweep():
    """Demonstrate parameter sweep generation."""
    print("\n" + "=" * 70)
    print("Parameter Sweep (Design of Experiments)")
    print("=" * 70)

    from koocad.hpc.parameter_sweep import ParameterSweep

    # Create parameter sweep
    print("\n1. Defining parameter space...")
    sweep = ParameterSweep()

    # Add parameters
    sweep.add_parameter("substrate_width", [10.0, 12.0, 14.0])
    sweep.add_parameter("ball_pitch", [0.6, 0.8, 1.0])
    sweep.add_range("ball_diameter", 0.3, 0.5, 3)

    print("   Parameters:")
    print(f"     - substrate_width: {sweep.parameters['substrate_width']}")
    print(f"     - ball_pitch: {sweep.parameters['ball_pitch']}")
    print(f"     - ball_diameter: {sweep.parameters['ball_diameter']}")

    # Generate different sampling strategies
    print("\n2. Generating samples...")

    # Cartesian (full factorial)
    cartesian = sweep.generate_cartesian()
    print(f"   ✓ Cartesian: {len(cartesian)} samples")

    # Random sampling
    random_samples = sweep.generate_random(n_samples=20, seed=42)
    print(f"   ✓ Random: {len(random_samples)} samples")

    # Sobol sequence (QMC)
    try:
        sobol = sweep.generate_sobol(n_samples=32)
        print(f"   ✓ Sobol: {len(sobol)} samples")
    except:
        print("   ⚠ Sobol: scipy not available")

    # Latin Hypercube
    try:
        lhs = sweep.generate_latin_hypercube(n_samples=20, seed=42)
        print(f"   ✓ Latin Hypercube: {len(lhs)} samples")
    except:
        print("   ⚠ LHS: scipy not available")

    # Save to JSON
    output_dir = Path("output/hpc")
    json_path = sweep.save_json(output_dir / "parameter_sweep.json")
    print(f"\n3. Saved to: {json_path}")

    # Statistics
    stats = sweep.get_statistics()
    print("\n4. Statistics:")
    print(f"   - Total samples: {stats['n_samples']}")
    print(f"   - Parameters: {stats['n_parameters']}")
    for param, param_stats in stats.get("parameters", {}).items():
        print(f"   - {param}:")
        for key, value in param_stats.items():
            print(f"       {key}: {value}")


def demo_job_array():
    """Demonstrate job array for parameter sweep."""
    print("\n" + "=" * 70)
    print("Job Array for Parameter Sweep")
    print("=" * 70)

    from koocad.hpc.slurm import SlurmJobGenerator
    from koocad.hpc.parameter_sweep import ParameterSweep

    print("\n1. Creating parameter sweep...")
    sweep = ParameterSweep()
    sweep.add_parameter("substrate_width", [10.0, 12.0, 14.0])
    sweep.add_parameter("ball_pitch", [0.6, 0.8, 1.0])
    samples = sweep.generate_cartesian()
    print(f"   ✓ Generated {len(samples)} parameter combinations")

    # Save sweep
    output_dir = Path("output/hpc")
    sweep.save_json(output_dir / "sweep.json")

    print("\n2. Creating job array script...")
    job = SlurmJobGenerator(
        job_name="koocad_sweep",
        partition="compute",
        cpus_per_task=4,
        mem_per_cpu="2G",
        time="01:00:00",
    )

    # Set array
    job.set_array(f"1-{len(samples)}")

    # Add commands to read parameter from JSON
    job.add_command("# Get parameters for this array task")
    job.add_command("PARAM_FILE=sweep.json")
    job.add_command('PARAMS=$(python -c "import json; data=json.load(open(\\"$PARAM_FILE\\")); print(json.dumps(data[\\"samples\\"][$SLURM_ARRAY_TASK_ID-1]))")')
    job.add_command("")
    job.add_command("# Run CAD generation with parameters")
    job.add_command('python generate_cad.py --params "$PARAMS" --output "result_${SLURM_ARRAY_TASK_ID}.json"')

    script_path = job.generate(output_dir / "job_array.sh")
    print(f"   ✓ Generated: {script_path}")


def demo_apptainer():
    """Demonstrate Apptainer container building."""
    print("\n" + "=" * 70)
    print("Apptainer Container Building")
    print("=" * 70)

    from koocad.hpc.apptainer import ApptainerBuilder

    print("\n1. Creating KooCAD container definition...")
    builder = ApptainerBuilder.create_koocad_container()

    # Customize further
    builder.add_post_command("# Additional setup")
    builder.add_post_command("pip3 install gmsh")

    # Generate definition file
    output_dir = Path("output/hpc")
    def_file = builder.generate_definition(output_dir / "koocad.def")
    print(f"   ✓ Generated: {def_file}")

    print("\n2. Definition file content (excerpt):")
    with open(def_file, "r") as f:
        lines = f.readlines()
        for line in lines[:30]:
            print(f"   {line.rstrip()}")

    print("\n3. To build the container:")
    print("   apptainer build --fakeroot koocad.sif koocad.def")
    print("\n4. To run:")
    print("   apptainer exec koocad.sif python script.py")


def demo_monitoring():
    """Demonstrate job monitoring."""
    print("\n" + "=" * 70)
    print("Job Monitoring")
    print("=" * 70)

    from koocad.hpc.monitoring import JobMonitor

    print("\n1. Creating job monitor...")
    monitor = JobMonitor()

    print("\n2. Query capabilities:")
    print("   - monitor.query_job(job_id)")
    print("   - monitor.query_jobs(user='username')")
    print("   - monitor.get_job_efficiency(job_id)")
    print("   - monitor.cancel_job(job_id)")
    print("   - monitor.wait_for_completion([job_ids])")

    print("\n3. Note: Requires Slurm commands (squeue, scontrol, seff)")
    print("   These are not available in demo environment")

    # Create mock statistics
    monitor.jobs = {
        1001: {"job_id": 1001, "state": "RUNNING", "cpus": 8, "nodes": 1},
        1002: {"job_id": 1002, "state": "COMPLETED", "cpus": 4, "nodes": 1},
        1003: {"job_id": 1003, "state": "PENDING", "cpus": 16, "nodes": 2},
    }

    stats = monitor.get_statistics()
    print("\n4. Example statistics:")
    print(f"   Total jobs: {stats['total_jobs']}")
    print(f"   States: {stats['states']}")
    print(f"   Total CPUs: {stats['total_cpus']}")
    print(f"   Total nodes: {stats['total_nodes']}")


def demo_aggregation():
    """Demonstrate result aggregation."""
    print("\n" + "=" * 70)
    print("Result Aggregation and Analysis")
    print("=" * 70)

    from koocad.hpc.aggregation import ResultAggregator

    print("\n1. Creating result aggregator...")
    aggregator = ResultAggregator()

    # Add mock results
    print("\n2. Adding mock results...")
    for i in range(20):
        substrate_width = 10.0 + i * 0.5
        ball_pitch = 0.6 + i * 0.02

        # Simulate output (volume)
        volume = substrate_width ** 2 * 0.8 + ball_pitch * 100

        aggregator.add_result(
            job_id=2000 + i,
            parameters={
                "substrate_width": substrate_width,
                "ball_pitch": ball_pitch,
            },
            outputs={
                "volume": volume,
                "surface_area": volume * 5.2,
            },
            status="SUCCESS",
        )

    # Add some failed results
    aggregator.add_result(
        job_id=2100,
        parameters={"substrate_width": 8.0, "ball_pitch": 0.5},
        outputs={},
        status="FAILED",
        error="Invalid parameters",
    )

    print(f"   ✓ Added {len(aggregator.results)} results")

    # Statistics
    print("\n3. Computing statistics...")
    volume_stats = aggregator.compute_statistics("volume")
    print(f"   Volume statistics:")
    for key, value in volume_stats.items():
        print(f"     {key}: {value:.3f}")

    # Find optimal
    optimal = aggregator.find_optimal("volume", minimize=True)
    if optimal:
        print(f"\n4. Optimal result (minimum volume):")
        print(f"   Job ID: {optimal['job_id']}")
        print(f"   Parameters: {optimal['parameters']}")
        print(f"   Volume: {optimal['outputs']['volume']:.3f}")

    # Summary
    summary = aggregator.generate_summary()
    print(f"\n5. Summary:")
    print(f"   Success rate: {summary['success_rate']*100:.1f}%")
    print(f"   Successful: {summary['successful']}")
    print(f"   Failed: {summary['failed']}")

    # Export
    output_dir = Path("output/hpc")
    csv_path = aggregator.export_csv(output_dir / "results.csv")
    json_path = aggregator.export_json(output_dir / "results.json")
    print(f"\n6. Exported results:")
    print(f"   CSV: {csv_path}")
    print(f"   JSON: {json_path}")

    # Generate plots
    print(f"\n7. Generating plots...")
    try:
        plot_path = aggregator.plot_1d(
            "substrate_width",
            "volume",
            output_dir / "volume_vs_width.png",
        )
        if plot_path:
            print(f"   ✓ 1D plot: {plot_path}")

        plot_2d_path = aggregator.plot_2d(
            "substrate_width",
            "ball_pitch",
            "volume",
            output_dir / "volume_2d.png",
        )
        if plot_2d_path:
            print(f"   ✓ 2D plot: {plot_2d_path}")
    except:
        print("   ⚠ Matplotlib not available")


def main():
    """Run all HPC demos."""
    print("=" * 70)
    print("KooCAD HPC Batch System Demo")
    print("=" * 70)
    print("\n🎉 Phase 136-145 Complete (FINAL PHASE)!")
    print("\nFull HPC Integration:")
    print("  ✓ Slurm job script generator")
    print("  ✓ Parameter sweep (Cartesian, Random, Sobol, LHS)")
    print("  ✓ Job arrays for parameter studies")
    print("  ✓ Apptainer container builder")
    print("  ✓ Job monitoring and tracking")
    print("  ✓ Result aggregation and analysis")
    print("  ✓ Visualization and reporting")
    print("\n🎊 Progress: 145/145 phases (100%)")
    print("🎊 PROJECT COMPLETE!")
    print("=" * 70)

    # Run demos
    demo_slurm_job()
    demo_parameter_sweep()
    demo_job_array()
    demo_apptainer()
    demo_monitoring()
    demo_aggregation()

    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print("\nOutput files created in:")
    print("  - output/hpc/ (scripts, containers, results)")
    print("\nNext steps:")
    print("  1. Submit jobs to Slurm: sbatch job_single.sh")
    print("  2. Monitor: squeue -u $USER")
    print("  3. Build container: apptainer build koocad.sif koocad.def")
    print("  4. Run parameter sweep: sbatch job_array.sh")
    print("  5. Aggregate results: python aggregate.py")
    print("\n🎉 All 145 phases implemented successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
