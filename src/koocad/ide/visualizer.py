"""
Dependency graph visualization for parameter sets.

This module provides tools to visualize parameter dependencies
as directed graphs using graphviz.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

try:
    import graphviz
except ImportError:
    graphviz = None  # type: ignore

from koocad.core.parameters import ExpressionParameter, ParameterSet


class DependencyVisualizer:
    """Visualize parameter dependency graphs."""

    def __init__(self, param_set: ParameterSet) -> None:
        """Initialize visualizer.

        Args:
            param_set: ParameterSet to visualize.
        """
        if graphviz is None:
            raise ImportError("graphviz is required for visualization. Install with: pip install graphviz")

        self.param_set = param_set

    def build_dependency_graph(self) -> Dict[str, List[str]]:
        """Build dependency graph as adjacency list.

        Returns:
            Dictionary mapping parameter names to their dependencies.
        """
        graph: Dict[str, List[str]] = {}

        for name, param in self.param_set.parameters.items():
            if isinstance(param, ExpressionParameter):
                graph[name] = list(param.dependencies)
            else:
                graph[name] = []

        return graph

    def find_roots(self, graph: Dict[str, List[str]]) -> List[str]:
        """Find root parameters (no dependencies).

        Args:
            graph: Dependency graph.

        Returns:
            List of root parameter names.
        """
        return [name for name, deps in graph.items() if not deps]

    def find_leaves(self, graph: Dict[str, List[str]]) -> List[str]:
        """Find leaf parameters (not used by others).

        Args:
            graph: Dependency graph.

        Returns:
            List of leaf parameter names.
        """
        all_deps = set()
        for deps in graph.values():
            all_deps.update(deps)

        return [name for name in graph.keys() if name not in all_deps]

    def topological_sort(self, graph: Dict[str, List[str]]) -> Optional[List[str]]:
        """Perform topological sort on dependency graph.

        Args:
            graph: Dependency graph.

        Returns:
            Sorted list of parameter names, or None if cycle exists.
        """
        # Compute in-degree for each node
        in_degree: Dict[str, int] = {name: 0 for name in graph.keys()}

        for deps in graph.values():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] += 1

        # Queue of nodes with no incoming edges
        queue = [name for name, degree in in_degree.items() if degree == 0]
        sorted_list = []

        while queue:
            node = queue.pop(0)
            sorted_list.append(node)

            # Reduce in-degree of neighbors
            for neighbor in graph[node]:
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        # Check for cycles
        if len(sorted_list) != len(graph):
            return None  # Cycle detected

        return sorted_list

    def detect_cycles(self, graph: Dict[str, List[str]]) -> List[List[str]]:
        """Detect cycles in dependency graph.

        Args:
            graph: Dependency graph.

        Returns:
            List of cycles (each cycle is a list of parameter names).
        """
        cycles: List[List[str]] = []
        visited: Set[str] = set()

        def dfs(node: str, path: List[str]) -> None:
            """DFS to detect cycles."""
            if node in path:
                # Found cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                if cycle not in cycles:
                    cycles.append(cycle)
                return

            if node in visited:
                return

            visited.add(node)

            for neighbor in graph.get(node, []):
                dfs(neighbor, path + [node])

        for node in graph.keys():
            dfs(node, [])

        return cycles

    def render_graph(
        self,
        output_path: Optional[Path] = None,
        format: str = "png",
        show_values: bool = False,
        highlight_cycles: bool = True,
    ) -> graphviz.Digraph:
        """Render dependency graph using graphviz.

        Args:
            output_path: Path to save output file (without extension).
            format: Output format (png, pdf, svg, etc.).
            show_values: If True, show parameter values in nodes.
            highlight_cycles: If True, highlight cyclic dependencies in red.

        Returns:
            Graphviz Digraph object.
        """
        dot = graphviz.Digraph(comment="Parameter Dependencies")
        dot.attr(rankdir="LR")  # Left to right layout

        graph = self.build_dependency_graph()
        cycles = self.detect_cycles(graph) if highlight_cycles else []
        cycle_edges = set()

        # Build set of edges that are part of cycles
        for cycle in cycles:
            for i in range(len(cycle) - 1):
                cycle_edges.add((cycle[i], cycle[i + 1]))

        # Add nodes
        for name, param in self.param_set.parameters.items():
            label = name
            if show_values:
                label += f"\n{param.value}"

            # Color nodes based on type
            if isinstance(param, ExpressionParameter):
                dot.node(name, label, shape="box", style="filled", fillcolor="lightblue")
            else:
                dot.node(name, label, shape="ellipse", style="filled", fillcolor="lightgreen")

        # Add edges
        for name, deps in graph.items():
            for dep in deps:
                # Highlight cycle edges in red
                if (name, dep) in cycle_edges:
                    dot.edge(dep, name, color="red", penwidth="2.0")
                else:
                    dot.edge(dep, name)

        # Render to file if path provided
        if output_path:
            dot.render(str(output_path), format=format, cleanup=True)

        return dot

    def render_subgraph(
        self,
        param_name: str,
        depth: int = 2,
        output_path: Optional[Path] = None,
        format: str = "png",
    ) -> graphviz.Digraph:
        """Render subgraph around a specific parameter.

        Args:
            param_name: Root parameter for subgraph.
            depth: Maximum depth to traverse.
            output_path: Path to save output file.
            format: Output format.

        Returns:
            Graphviz Digraph object.
        """
        dot = graphviz.Digraph(comment=f"Dependencies of {param_name}")
        dot.attr(rankdir="LR")

        # BFS to collect nodes within depth
        visited = {param_name}
        queue = [(param_name, 0)]
        nodes_to_include = set()

        while queue:
            node, d = queue.pop(0)
            nodes_to_include.add(node)

            if d < depth:
                param = self.param_set.get(node)
                if isinstance(param, ExpressionParameter):
                    for dep in param.dependencies:
                        if dep not in visited:
                            visited.add(dep)
                            queue.append((dep, d + 1))

        # Add nodes
        for name in nodes_to_include:
            param = self.param_set.get(name)
            if param is None:
                continue

            label = f"{name}\n{param.value}"

            if isinstance(param, ExpressionParameter):
                dot.node(name, label, shape="box", style="filled", fillcolor="lightblue")
            else:
                dot.node(name, label, shape="ellipse", style="filled", fillcolor="lightgreen")

        # Add edges
        for name in nodes_to_include:
            param = self.param_set.get(name)
            if isinstance(param, ExpressionParameter):
                for dep in param.dependencies:
                    if dep in nodes_to_include:
                        dot.edge(dep, name)

        if output_path:
            dot.render(str(output_path), format=format, cleanup=True)

        return dot

    def generate_report(self) -> Dict[str, any]:
        """Generate comprehensive dependency analysis report.

        Returns:
            Dictionary with analysis results.
        """
        graph = self.build_dependency_graph()

        report = {
            "total_parameters": len(self.param_set.parameters),
            "expression_parameters": sum(
                1 for p in self.param_set.parameters.values() if isinstance(p, ExpressionParameter)
            ),
            "root_parameters": self.find_roots(graph),
            "leaf_parameters": self.find_leaves(graph),
            "cycles": self.detect_cycles(graph),
            "topological_order": self.topological_sort(graph),
        }

        # Compute complexity metrics
        total_deps = sum(len(deps) for deps in graph.values())
        report["average_dependencies"] = total_deps / len(graph) if graph else 0

        max_deps = max((len(deps) for deps in graph.values()), default=0)
        report["max_dependencies"] = max_deps

        return report

    def print_report(self) -> None:
        """Print dependency analysis report to console."""
        from rich.console import Console
        from rich.table import Table

        console = Console()
        report = self.generate_report()

        # Overview table
        table = Table(title="Dependency Analysis Report")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Parameters", str(report["total_parameters"]))
        table.add_row("Expression Parameters", str(report["expression_parameters"]))
        table.add_row("Root Parameters", str(len(report["root_parameters"])))
        table.add_row("Leaf Parameters", str(len(report["leaf_parameters"])))
        table.add_row("Cycles Detected", str(len(report["cycles"])))
        table.add_row("Average Dependencies", f"{report['average_dependencies']:.2f}")
        table.add_row("Max Dependencies", str(report["max_dependencies"]))

        console.print(table)

        # Show cycles if any
        if report["cycles"]:
            console.print("\n[red]⚠ Circular Dependencies Detected:[/red]")
            for i, cycle in enumerate(report["cycles"], 1):
                console.print(f"  {i}. {' → '.join(cycle)}")

        # Show topological order
        if report["topological_order"]:
            console.print(f"\n[green]✓ Valid Topological Order:[/green]")
            console.print(f"  {' → '.join(report['topological_order'])}")
        else:
            console.print("\n[red]✗ No valid topological order (cycles exist)[/red]")
