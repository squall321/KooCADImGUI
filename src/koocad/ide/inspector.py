"""
Parameter inspector for debugging and analysis.

This module provides tools to inspect parameter values, dependencies,
and validation states.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from koocad.core.parameters import ExpressionParameter, FloatParameter, IntParameter, Parameter, ParameterSet


class ParameterInspector:
    """Inspector for debugging parameter sets."""

    def __init__(self, param_set: ParameterSet) -> None:
        """Initialize inspector.

        Args:
            param_set: ParameterSet to inspect.
        """
        self.param_set = param_set
        self.console = Console()

    def inspect(self, param_name: str) -> Dict[str, Any]:
        """Inspect a single parameter.

        Args:
            param_name: Parameter name to inspect.

        Returns:
            Dictionary with inspection results.
        """
        param = self.param_set.get(param_name)
        if param is None:
            return {"error": f"Parameter '{param_name}' not found"}

        info: Dict[str, Any] = {
            "name": param.name,
            "type": param.__class__.__name__,
            "value": param.value,
            "description": param.description,
        }

        # Type-specific information
        if isinstance(param, FloatParameter):
            info.update(
                {
                    "min_value": param.min_value,
                    "max_value": param.max_value,
                    "unit": param.unit.value if param.unit else None,
                    "base_unit_value": param.to_base_unit(),
                }
            )

            # Validation status
            is_valid = True
            issues = []

            if param.min_value is not None and param.value < param.min_value:
                is_valid = False
                issues.append(f"Value {param.value} is below minimum {param.min_value}")

            if param.max_value is not None and param.value > param.max_value:
                is_valid = False
                issues.append(f"Value {param.value} exceeds maximum {param.max_value}")

            info["validation"] = {
                "is_valid": is_valid,
                "issues": issues,
            }

        elif isinstance(param, IntParameter):
            info.update(
                {
                    "min_value": param.min_value,
                    "max_value": param.max_value,
                }
            )

        elif isinstance(param, ExpressionParameter):
            info.update(
                {
                    "expression": param.value,
                    "dependencies": param.dependencies,
                }
            )

            # Try to evaluate
            try:
                evaluated = param.evaluate(self.param_set.evaluate_all())
                info["evaluated_value"] = evaluated
            except Exception as e:
                info["evaluation_error"] = str(e)

        return info

    def print_parameter(self, param_name: str) -> None:
        """Pretty-print parameter information.

        Args:
            param_name: Parameter name to print.
        """
        info = self.inspect(param_name)

        if "error" in info:
            self.console.print(f"[red]Error: {info['error']}[/red]")
            return

        table = Table(title=f"Parameter: {param_name}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        for key, value in info.items():
            if isinstance(value, dict):
                # Nested dict
                table.add_row(key, str(value))
            elif isinstance(value, list):
                # List
                table.add_row(key, ", ".join(str(v) for v in value))
            else:
                table.add_row(key, str(value))

        self.console.print(table)

    def print_all_parameters(self, detailed: bool = False) -> None:
        """Print all parameters in parameter set.

        Args:
            detailed: If True, show detailed information.
        """
        table = Table(title="Parameter Set Overview")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("Value", style="green")

        if detailed:
            table.add_column("Details", style="dim")

        for name, param in self.param_set.parameters.items():
            row = [name, param.__class__.__name__, str(param.value)]

            if detailed:
                details = []
                if isinstance(param, FloatParameter):
                    if param.min_value is not None:
                        details.append(f"min={param.min_value}")
                    if param.max_value is not None:
                        details.append(f"max={param.max_value}")
                    if param.unit:
                        details.append(f"unit={param.unit.value}")
                elif isinstance(param, ExpressionParameter):
                    details.append(f"deps={len(param.dependencies)}")

                row.append(", ".join(details))

            table.add_row(*row)

        self.console.print(table)

    def print_dependency_tree(self, root_param: Optional[str] = None) -> None:
        """Print dependency tree for parameters.

        Args:
            root_param: Root parameter name (if None, show all).
        """
        if root_param:
            param = self.param_set.get(root_param)
            if param is None:
                self.console.print(f"[red]Parameter '{root_param}' not found[/red]")
                return

            tree = Tree(f"[cyan]{root_param}[/cyan]")
            self._add_dependencies_to_tree(tree, root_param, visited=set())
            self.console.print(tree)
        else:
            # Show all parameters with dependencies
            tree = Tree("[bold]Parameter Dependencies[/bold]")

            for name, param in self.param_set.parameters.items():
                if isinstance(param, ExpressionParameter) and param.dependencies:
                    param_tree = tree.add(f"[cyan]{name}[/cyan]")
                    self._add_dependencies_to_tree(param_tree, name, visited=set())

            self.console.print(tree)

    def _add_dependencies_to_tree(self, tree: Tree, param_name: str, visited: set[str]) -> None:
        """Recursively add dependencies to tree.

        Args:
            tree: Rich Tree object.
            param_name: Parameter name.
            visited: Set of visited parameters (cycle detection).
        """
        if param_name in visited:
            tree.add(f"[red]{param_name} (circular!)[/red]")
            return

        visited.add(param_name)

        param = self.param_set.get(param_name)
        if isinstance(param, ExpressionParameter):
            for dep in param.dependencies:
                dep_tree = tree.add(f"[yellow]{dep}[/yellow]")
                self._add_dependencies_to_tree(dep_tree, dep, visited.copy())

    def find_unused_parameters(self) -> List[str]:
        """Find parameters that are not used by any expressions.

        Returns:
            List of unused parameter names.
        """
        # Collect all referenced parameters
        referenced = set()

        for param in self.param_set.parameters.values():
            if isinstance(param, ExpressionParameter):
                referenced.update(param.dependencies)

        # Find parameters not in referenced set
        all_params = set(self.param_set.parameters.keys())
        unused = all_params - referenced

        return list(unused)

    def find_circular_dependencies(self) -> List[List[str]]:
        """Find circular dependencies in parameter set.

        Returns:
            List of circular dependency chains.
        """
        cycles: List[List[str]] = []

        def visit(param_name: str, path: List[str]) -> None:
            """DFS to detect cycles."""
            if param_name in path:
                # Found cycle
                cycle_start = path.index(param_name)
                cycle = path[cycle_start:] + [param_name]
                if cycle not in cycles:
                    cycles.append(cycle)
                return

            param = self.param_set.get(param_name)
            if isinstance(param, ExpressionParameter):
                for dep in param.dependencies:
                    visit(dep, path + [param_name])

        # Check all expression parameters
        for name, param in self.param_set.parameters.items():
            if isinstance(param, ExpressionParameter):
                visit(name, [])

        return cycles

    def validate_all(self) -> Dict[str, List[str]]:
        """Validate all parameters and return issues.

        Returns:
            Dictionary mapping parameter names to validation issues.
        """
        issues: Dict[str, List[str]] = {}

        for name, param in self.param_set.parameters.items():
            param_issues = []

            # Type-specific validation
            if isinstance(param, FloatParameter):
                if param.min_value is not None and param.value < param.min_value:
                    param_issues.append(f"Value {param.value} is below minimum {param.min_value}")

                if param.max_value is not None and param.value > param.max_value:
                    param_issues.append(f"Value {param.value} exceeds maximum {param.max_value}")

            elif isinstance(param, IntParameter):
                if param.min_value is not None and param.value < param.min_value:
                    param_issues.append(f"Value {param.value} is below minimum {param.min_value}")

                if param.max_value is not None and param.value > param.max_value:
                    param_issues.append(f"Value {param.value} exceeds maximum {param.max_value}")

            elif isinstance(param, ExpressionParameter):
                # Check dependencies exist
                for dep in param.dependencies:
                    if dep not in self.param_set.parameters:
                        param_issues.append(f"Dependency '{dep}' not found")

                # Try evaluation
                try:
                    param.evaluate(self.param_set.evaluate_all())
                except Exception as e:
                    param_issues.append(f"Evaluation failed: {e}")

            if param_issues:
                issues[name] = param_issues

        return issues
