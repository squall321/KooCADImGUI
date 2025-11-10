#!/usr/bin/env python
"""
KooCAD CLI - Command-line interface for KooCAD system.

This module provides the main CLI entry point using Click.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from koocad import __version__

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="koocad")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file",
)
@click.pass_context
def cli(ctx: click.Context, config: Optional[str]) -> None:
    """KooCAD - Parametric Electronic Component CAD Automation System.

    A comprehensive framework for generating parametric 3D CAD models
    of electronic components with HPC batch processing.
    """
    ctx.ensure_object(dict)
    if config:
        ctx.obj["config"] = Path(config)


@cli.command()
@click.option("--params", "-p", type=click.Path(exists=True), required=True, help="Parameter JSON file")
@click.option("--output", "-o", type=click.Path(), required=True, help="Output directory")
@click.option(
    "--format",
    "-f",
    multiple=True,
    type=click.Choice(["step", "iges", "stl", "glb", "dyna"]),
    default=["step"],
    help="Output formats (can specify multiple)",
)
@click.option("--kernel", type=click.Choice(["cadquery", "occt"]), default="cadquery", help="CAD kernel to use")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def generate(
    params: str,
    output: str,
    format: tuple[str, ...],
    kernel: str,
    verbose: bool,
) -> None:
    """Generate CAD model from parameter file.

    Example:
        koocad generate -p params.json -o output/ -f step -f stl
    """
    import json

    from koocad.utils.logging import get_logger, setup_logging

    # Setup logging
    setup_logging(log_level="DEBUG" if verbose else "INFO", json_format=False)
    logger = get_logger(__name__)

    logger.info("Starting CAD generation", params_file=params, output_dir=output)

    try:
        # Load parameters
        with open(params) as f:
            param_data = json.load(f)

        logger.info("Parameters loaded", param_count=len(param_data))

        # Create output directory
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)

        # TODO: Actual CAD generation (Phase 31-50)
        console.print(f"[green]✓[/green] Parameters loaded: {len(param_data)} parameters")
        console.print(f"[green]✓[/green] Output directory: {output_path}")
        console.print(f"[yellow]⚠[/yellow] CAD generation not yet implemented (Phase 31-50)")
        console.print(f"[dim]  Kernel: {kernel}[/dim]")
        console.print(f"[dim]  Formats: {', '.join(format)}[/dim]")

        logger.info("Generation complete (placeholder)")

    except Exception as e:
        logger.error("Generation failed", error=str(e))
        console.print(f"[red]✗[/red] Error: {e}")
        sys.exit(1)


@cli.group()
def sweep() -> None:
    """Parameter sweep operations."""
    pass


@sweep.command("generate")
@click.option("--config", "-c", type=click.Path(exists=True), required=True, help="Sweep config YAML")
@click.option("--output", "-o", type=click.Path(), required=True, help="Output directory for parameter files")
@click.option("--count", type=int, help="Number of samples (for random sweep)")
def sweep_generate(config: str, output: str, count: Optional[int]) -> None:
    """Generate parameter sweep files.

    Example:
        koocad sweep generate -c sweep.yaml -o params/
    """
    import json

    import yaml

    from koocad.testing.factories import ParameterSweepFactory

    # Load config
    with open(config) as f:
        sweep_config = yaml.safe_load(f)

    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)

    sweep_type = sweep_config.get("sweep_type", "cartesian")

    if sweep_type == "cartesian":
        param_ranges = sweep_config.get("parameters", {})
        sweep_data = ParameterSweepFactory.create_cartesian_sweep(param_ranges)
    elif sweep_type == "random":
        param_ranges = {
            k: tuple(v) for k, v in sweep_config.get("parameters", {}).items()
        }
        n_samples = count or sweep_config.get("n_samples", 100)
        sweep_data = ParameterSweepFactory.create_random_sweep(param_ranges, n_samples)
    else:
        console.print(f"[red]✗[/red] Unknown sweep type: {sweep_type}")
        sys.exit(1)

    # Save parameter files
    for i, params in enumerate(sweep_data):
        param_file = output_path / f"params_{i}.json"
        with open(param_file, "w") as f:
            json.dump(params, f, indent=2)

    console.print(f"[green]✓[/green] Generated {len(sweep_data)} parameter files")
    console.print(f"[dim]  Output: {output_path}/params_*.json[/dim]")


@cli.command()
@click.option("--host", default="0.0.0.0", help="Server host")
@click.option("--port", default=8000, type=int, help="Server port")
@click.option("--reload", is_flag=True, help="Auto-reload on code changes")
def server(host: str, port: int, reload: bool) -> None:
    """Start FastAPI server.

    Example:
        koocad server --host 0.0.0.0 --port 8000 --reload
    """
    import uvicorn

    console.print(f"[cyan]Starting KooCAD API server...[/cyan]")
    console.print(f"[dim]  Host: {host}[/dim]")
    console.print(f"[dim]  Port: {port}[/dim]")
    console.print(f"[dim]  Reload: {reload}[/dim]")

    # TODO: Implement FastAPI app (Phase 106-120)
    console.print(f"[yellow]⚠[/yellow] API server not yet implemented (Phase 106-120)")


@cli.command()
def info() -> None:
    """Display system information."""
    import platform

    from koocad.config import get_settings

    settings = get_settings()

    table = Table(title="KooCAD System Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Version", __version__)
    table.add_row("Python", platform.python_version())
    table.add_row("Platform", platform.system())
    table.add_row("Environment", settings.environment)
    table.add_row("CAD Kernel", settings.cad.default_kernel)
    table.add_row("Mesh Engine", settings.mesh.default_engine)
    table.add_row("Database", settings.database.url.split("@")[-1])

    console.print(table)


@cli.command()
@click.argument("name")
@click.option("--output", "-o", type=click.Path(), default=".", help="Output directory")
def init(name: str, output: str) -> None:
    """Initialize a new KooCAD project.

    Example:
        koocad init my_project -o ~/projects/
    """
    from koocad.utils.logging import get_logger, setup_logging

    setup_logging(log_level="INFO", json_format=False)
    logger = get_logger(__name__)

    project_path = Path(output) / name
    project_path.mkdir(parents=True, exist_ok=True)

    # Create project structure
    dirs = [
        "params",
        "results",
        "scripts",
        "config",
    ]

    for dir_name in dirs:
        (project_path / dir_name).mkdir(exist_ok=True)

    # Create sample files
    sample_param = {
        "component_type": "bga",
        "substrate_width": 12.0,
        "substrate_height": 12.0,
        "ball_pitch": 0.8,
    }

    with open(project_path / "params" / "sample.json", "w") as f:
        import json
        json.dump(sample_param, f, indent=2)

    # Create README
    readme = f"""# {name}

KooCAD project for parametric CAD generation.

## Structure

- `params/` - Parameter files
- `results/` - Generated CAD files
- `scripts/` - Custom scripts
- `config/` - Configuration files

## Usage

```bash
# Generate CAD model
koocad generate -p params/sample.json -o results/

# Parameter sweep
koocad sweep generate -c sweep.yaml -o params/
```
"""

    with open(project_path / "README.md", "w") as f:
        f.write(readme)

    console.print(f"[green]✓[/green] Project initialized: {project_path}")
    logger.info("Project created", path=str(project_path))


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
