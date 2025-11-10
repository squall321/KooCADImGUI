"""
Graph execution engine for node-based visual programming.

This module implements topological sorting, caching, and execution
of node graphs.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from koocad.core.parameters import ParameterSet
from koocad.generators.base import ComponentGenerator, GenerationContext
from koocad.kernels.base import Shape


class NodeStatus(Enum):
    """Node execution status."""

    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    ERROR = "error"
    CACHED = "cached"


@dataclass
class ExecutionResult:
    """Result of node execution."""

    node_id: int
    status: NodeStatus
    output: Any
    execution_time: float
    error: Optional[str] = None
    cached: bool = False


@dataclass
class GraphExecutionContext:
    """Context for graph execution."""

    values: Dict[int, Any] = field(default_factory=dict)  # pin_id -> value
    cache: Dict[int, ExecutionResult] = field(default_factory=dict)  # node_id -> result
    errors: List[str] = field(default_factory=list)
    execution_order: List[int] = field(default_factory=list)


class GraphExecutor:
    """Execute node graphs in correct dependency order."""

    def __init__(self) -> None:
        """Initialize graph executor."""
        self.context = GraphExecutionContext()
        self.use_cache = True

    def topological_sort(
        self,
        nodes: Dict[int, Any],
        links: List[tuple[int, int]],
    ) -> Optional[List[int]]:
        """Perform topological sort on node graph.

        Args:
            nodes: Dictionary of node_id -> node.
            links: List of (from_pin, to_pin) tuples.

        Returns:
            Sorted list of node IDs, or None if cycle detected.
        """
        # Build adjacency list: node_id -> [dependent_node_ids]
        adjacency: Dict[int, Set[int]] = {node_id: set() for node_id in nodes.keys()}
        in_degree: Dict[int, int] = {node_id: 0 for node_id in nodes.keys()}

        # Map pins to nodes
        pin_to_node: Dict[int, int] = {}
        for node_id, node in nodes.items():
            for pin_id in node.inputs + node.outputs:
                pin_to_node[pin_id] = node_id

        # Build graph from links
        for from_pin, to_pin in links:
            if from_pin in pin_to_node and to_pin in pin_to_node:
                from_node = pin_to_node[from_pin]
                to_node = pin_to_node[to_pin]

                if from_node != to_node:
                    adjacency[from_node].add(to_node)
                    in_degree[to_node] += 1

        # Kahn's algorithm for topological sort
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        sorted_nodes = []

        while queue:
            node_id = queue.popleft()
            sorted_nodes.append(node_id)

            for dependent in adjacency[node_id]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Check for cycles
        if len(sorted_nodes) != len(nodes):
            return None  # Cycle detected

        return sorted_nodes

    def collect_node_inputs(
        self,
        node: Any,
        links: List[tuple[int, int]],
    ) -> Dict[str, Any]:
        """Collect input values for a node.

        Args:
            node: Node to collect inputs for.
            links: List of links in graph.

        Returns:
            Dictionary of input_name -> value.
        """
        inputs = {}

        # For each input pin, find connected output pin
        for i, input_pin in enumerate(node.inputs):
            input_name = node.get_inputs()[i] if i < len(node.get_inputs()) else f"input_{i}"

            # Find link connected to this input
            for from_pin, to_pin in links:
                if to_pin == input_pin and from_pin in self.context.values:
                    inputs[input_name] = self.context.values[from_pin]
                    break

        return inputs

    def execute_node(
        self,
        node: Any,
        inputs: Dict[str, Any],
    ) -> ExecutionResult:
        """Execute a single node.

        Args:
            node: Node to execute.
            inputs: Input values for node.

        Returns:
            Execution result.
        """
        # Check cache
        if self.use_cache and node.node_id in self.context.cache:
            cached_result = self.context.cache[node.node_id]
            # TODO: Check if inputs changed
            return ExecutionResult(
                node_id=node.node_id,
                status=NodeStatus.CACHED,
                output=cached_result.output,
                execution_time=0.0,
                cached=True,
            )

        start_time = datetime.now()

        try:
            # Execute node
            outputs = node.execute(inputs)

            execution_time = (datetime.now() - start_time).total_seconds()

            # Store output values
            if outputs and len(node.outputs) > 0:
                output_names = node.get_outputs()
                for i, output_pin in enumerate(node.outputs):
                    if i < len(output_names):
                        output_name = output_names[i]
                        if output_name in outputs:
                            self.context.values[output_pin] = outputs[output_name]

            result = ExecutionResult(
                node_id=node.node_id,
                status=NodeStatus.COMPLETED,
                output=outputs,
                execution_time=execution_time,
            )

            # Cache result
            self.context.cache[node.node_id] = result

            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()

            error_msg = f"Node {node.node_id} ({node.label}): {str(e)}"
            self.context.errors.append(error_msg)

            return ExecutionResult(
                node_id=node.node_id,
                status=NodeStatus.ERROR,
                output=None,
                execution_time=execution_time,
                error=error_msg,
            )

    def execute_graph(
        self,
        nodes: Dict[int, Any],
        links: List[tuple[int, int]],
        clear_cache: bool = False,
    ) -> GraphExecutionContext:
        """Execute entire node graph.

        Args:
            nodes: Dictionary of nodes.
            links: List of links.
            clear_cache: If True, clear cache before execution.

        Returns:
            Execution context with results.
        """
        if clear_cache:
            self.context = GraphExecutionContext()

        # Topological sort
        execution_order = self.topological_sort(nodes, links)

        if execution_order is None:
            self.context.errors.append("Cycle detected in node graph!")
            return self.context

        self.context.execution_order = execution_order

        # Execute nodes in order
        for node_id in execution_order:
            if node_id not in nodes:
                continue

            node = nodes[node_id]

            # Collect inputs
            inputs = self.collect_node_inputs(node, links)

            # Execute node
            result = self.execute_node(node, inputs)

            print(f"Executed node {node_id} ({node.label}): {result.status.value} "
                  f"in {result.execution_time:.3f}s")

        return self.context

    def get_final_output(self) -> Optional[Any]:
        """Get final output from last executed node.

        Returns:
            Output value, or None if no output.
        """
        if not self.context.execution_order:
            return None

        # Get last node output
        last_node_id = self.context.execution_order[-1]
        if last_node_id in self.context.cache:
            return self.context.cache[last_node_id].output

        return None

    def clear_cache(self) -> None:
        """Clear execution cache."""
        self.context.cache.clear()
        self.context.values.clear()


class LivePreviewEngine:
    """Engine for live preview of CAD models during node editing."""

    def __init__(self) -> None:
        """Initialize live preview engine."""
        self.executor = GraphExecutor()
        self.current_shape: Optional[Shape] = None
        self.auto_execute = True
        self.debounce_timer = 0.5  # seconds

    def set_auto_execute(self, enabled: bool) -> None:
        """Enable or disable auto-execution on parameter change.

        Args:
            enabled: If True, automatically execute on changes.
        """
        self.auto_execute = enabled

    def execute_and_preview(
        self,
        nodes: Dict[int, Any],
        links: List[tuple[int, int]],
    ) -> Optional[Shape]:
        """Execute graph and return preview shape.

        Args:
            nodes: Node dictionary.
            links: Link list.

        Returns:
            Generated shape, or None on error.
        """
        context = self.executor.execute_graph(nodes, links)

        if context.errors:
            print("Execution errors:")
            for error in context.errors:
                print(f"  - {error}")
            return None

        # Get final shape output
        output = self.executor.get_final_output()

        if output and "Shape" in output:
            self.current_shape = output["Shape"]
            return self.current_shape

        return None

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics.

        Returns:
            Dictionary with execution stats.
        """
        context = self.executor.context

        total_time = sum(
            result.execution_time
            for result in context.cache.values()
            if not result.cached
        )

        cached_count = sum(1 for result in context.cache.values() if result.cached)

        return {
            "total_nodes": len(context.execution_order),
            "total_time": total_time,
            "cached_nodes": cached_count,
            "errors": len(context.errors),
            "execution_order": context.execution_order,
        }
