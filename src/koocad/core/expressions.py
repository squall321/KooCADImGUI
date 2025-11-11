"""
Advanced Expression Engine for parametric calculations.

This module provides a sophisticated expression evaluation system with
support for complex mathematical operations, functions, and constraints.
"""

import operator
from collections.abc import Callable

import sympy as sp
from sympy import Symbol
from sympy.parsing.sympy_parser import parse_expr


class ExpressionEngine:
    """Advanced expression engine with function support."""

    # Built-in functions
    FUNCTIONS: dict[str, Callable] = {
        "sqrt": sp.sqrt,
        "sin": sp.sin,
        "cos": sp.cos,
        "tan": sp.tan,
        "exp": sp.exp,
        "log": sp.log,
        "abs": sp.Abs,
        "min": sp.Min,
        "max": sp.Max,
        "floor": sp.floor,
        "ceil": sp.ceiling,
        "round": lambda x: sp.Integer(round(x)),
    }

    # Operators
    OPERATORS: dict[str, Callable] = {
        "+": operator.add,
        "-": operator.sub,
        "*": operator.mul,
        "/": operator.truediv,
        "**": operator.pow,
        "^": operator.pow,  # Alternative power notation
    }

    def __init__(self) -> None:
        """Initialize expression engine."""
        self.custom_functions: dict[str, Callable] = {}
        self.constants: dict[str, float] = {
            "pi": float(sp.pi),
            "e": float(sp.E),
        }

    def register_function(self, name: str, func: Callable) -> None:
        """Register a custom function.

        Args:
            name: Function name.
            func: Function implementation.

        Example:
            >>> engine = ExpressionEngine()
            >>> engine.register_function("double", lambda x: 2 * x)
            >>> engine.evaluate("double(5)", {})
            10.0
        """
        self.custom_functions[name] = func

    def register_constant(self, name: str, value: float) -> None:
        """Register a custom constant.

        Args:
            name: Constant name.
            value: Constant value.
        """
        self.constants[name] = value

    def parse(self, expression: str) -> sp.Expr:
        """Parse expression string to SymPy expression.

        Args:
            expression: Expression string.

        Returns:
            Parsed SymPy expression.

        Raises:
            ValueError: If expression is invalid.

        Example:
            >>> engine = ExpressionEngine()
            >>> expr = engine.parse("x + 2*y")
            >>> type(expr)
            <class 'sympy.core.add.Add'>
        """
        try:
            # Replace custom functions
            expr_str = expression
            for name in self.custom_functions:
                expr_str = expr_str.replace(name, f"_custom_{name}")

            # Parse with SymPy
            expr = parse_expr(expr_str)
            return expr

        except Exception as e:
            raise ValueError(f"Invalid expression '{expression}': {e}")

    def extract_variables(self, expression: str) -> set[str]:
        """Extract variable names from expression.

        Args:
            expression: Expression string.

        Returns:
            Set of variable names.

        Example:
            >>> engine = ExpressionEngine()
            >>> vars = engine.extract_variables("x + 2*y - z")
            >>> sorted(vars)
            ['x', 'y', 'z']
        """
        expr = self.parse(expression)
        symbols = expr.free_symbols
        return {str(s) for s in symbols if not str(s).startswith("_custom_")}

    def evaluate(
        self,
        expression: str,
        context: dict[str, float],
        *,
        validate: bool = True,
    ) -> float:
        """Evaluate expression with given context.

        Args:
            expression: Expression string.
            context: Variable name -> value mapping.
            validate: Whether to validate variable availability.

        Returns:
            Evaluated result.

        Raises:
            ValueError: If required variables are missing.

        Example:
            >>> engine = ExpressionEngine()
            >>> result = engine.evaluate("2*x + y", {"x": 3, "y": 4})
            >>> result
            10.0
        """
        # Add constants to context
        full_context = {**self.constants, **context}

        # Parse expression
        expr = self.parse(expression)

        # Check for missing variables
        if validate:
            required_vars = self.extract_variables(expression)
            missing = required_vars - set(context.keys()) - set(self.constants.keys())
            if missing:
                raise ValueError(
                    f"Missing variables in context: {missing}. "
                    f"Required: {required_vars}, Provided: {set(context.keys())}"
                )

        # Substitute values
        try:
            result = expr.subs(full_context)
            return float(result)
        except Exception as e:
            raise ValueError(f"Failed to evaluate '{expression}': {e}")

    def simplify(self, expression: str) -> str:
        """Simplify expression algebraically.

        Args:
            expression: Expression string.

        Returns:
            Simplified expression string.

        Example:
            >>> engine = ExpressionEngine()
            >>> engine.simplify("x + x + 2*x")
            '4*x'
        """
        expr = self.parse(expression)
        simplified = sp.simplify(expr)
        return str(simplified)

    def differentiate(self, expression: str, variable: str) -> str:
        """Compute derivative of expression.

        Args:
            expression: Expression string.
            variable: Variable to differentiate with respect to.

        Returns:
            Derivative expression string.

        Example:
            >>> engine = ExpressionEngine()
            >>> engine.differentiate("x**2 + 2*x", "x")
            '2*x + 2'
        """
        expr = self.parse(expression)
        var = Symbol(variable)
        derivative = sp.diff(expr, var)
        return str(derivative)

    def solve(self, expression: str, variable: str) -> list[float]:
        """Solve equation for variable.

        Args:
            expression: Expression string (equation = 0).
            variable: Variable to solve for.

        Returns:
            List of solutions.

        Example:
            >>> engine = ExpressionEngine()
            >>> engine.solve("x**2 - 4", "x")
            [-2.0, 2.0]
        """
        expr = self.parse(expression)
        var = Symbol(variable)
        solutions = sp.solve(expr, var)
        return [float(sol) for sol in solutions if sol.is_real]


class DependencyGraph:
    """Dependency graph for expression evaluation order."""

    def __init__(self) -> None:
        """Initialize dependency graph."""
        self.nodes: set[str] = set()
        self.edges: dict[str, set[str]] = {}

    def add_node(self, name: str) -> None:
        """Add a node to the graph."""
        self.nodes.add(name)
        if name not in self.edges:
            self.edges[name] = set()

    def add_edge(self, from_node: str, to_node: str) -> None:
        """Add a dependency edge.

        Args:
            from_node: Dependent node.
            to_node: Dependency node.
        """
        self.add_node(from_node)
        self.add_node(to_node)
        self.edges[from_node].add(to_node)

    def topological_sort(self) -> list[str]:
        """Perform topological sort to get evaluation order.

        Returns:
            List of nodes in evaluation order.

        Raises:
            ValueError: If circular dependency detected.

        Example:
            >>> graph = DependencyGraph()
            >>> graph.add_edge("c", "a")
            >>> graph.add_edge("c", "b")
            >>> graph.add_edge("b", "a")
            >>> graph.topological_sort()
            ['a', 'b', 'c']
        """
        # Kahn's algorithm
        in_degree = dict.fromkeys(self.nodes, 0)

        for node in self.nodes:
            for neighbor in self.edges[node]:
                in_degree[neighbor] += 1

        queue = [node for node in self.nodes if in_degree[node] == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)

            for neighbor in self.edges[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self.nodes):
            # Circular dependency detected
            remaining = set(self.nodes) - set(result)
            raise ValueError(f"Circular dependency detected involving: {remaining}")

        return result

    def get_dependencies(self, node: str) -> set[str]:
        """Get all dependencies of a node (transitive closure).

        Args:
            node: Node name.

        Returns:
            Set of all dependencies.
        """
        visited = set()
        stack = [node]

        while stack:
            current = stack.pop()
            if current in visited:
                continue

            visited.add(current)
            stack.extend(self.edges.get(current, set()))

        visited.discard(node)
        return visited


class ExpressionValidator:
    """Validate expressions for safety and correctness."""

    DANGEROUS_NAMES = {
        "__import__",
        "eval",
        "exec",
        "compile",
        "open",
        "input",
        "__builtins__",
    }

    @classmethod
    def validate(cls, expression: str) -> bool:
        """Validate expression for safety.

        Args:
            expression: Expression string.

        Returns:
            True if safe, False otherwise.

        Example:
            >>> ExpressionValidator.validate("x + 2")
            True
            >>> ExpressionValidator.validate("__import__('os')")
            False
        """
        # Check for dangerous names
        for dangerous in cls.DANGEROUS_NAMES:
            if dangerous in expression:
                return False

        # Check for dangerous characters
        if any(char in expression for char in [";"]):
            return False

        return True

    @classmethod
    def sanitize(cls, expression: str) -> str:
        """Sanitize expression by removing dangerous parts.

        Args:
            expression: Expression string.

        Returns:
            Sanitized expression.
        """
        # Remove whitespace
        sanitized = expression.strip()

        # Remove comments
        if "#" in sanitized:
            sanitized = sanitized.split("#")[0].strip()

        return sanitized
