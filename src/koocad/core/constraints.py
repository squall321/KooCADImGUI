"""
Constraint Satisfaction Problem (CSP) solver for parameters.

This module provides constraint solving capabilities for ensuring
parameter values satisfy all defined constraints.
"""

from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from koocad.core.parameters import Parameter


class Constraint:
    """Base class for constraints."""

    def __init__(self, variables: List[str], predicate: Callable[..., bool]) -> None:
        """Initialize constraint.

        Args:
            variables: List of variable names this constraint applies to.
            predicate: Function that returns True if constraint is satisfied.
        """
        self.variables = variables
        self.predicate = predicate

    def is_satisfied(self, assignment: Dict[str, Any]) -> bool:
        """Check if constraint is satisfied with given assignment.

        Args:
            assignment: Variable -> value mapping.

        Returns:
            True if constraint is satisfied.
        """
        values = [assignment.get(var) for var in self.variables]
        if any(v is None for v in values):
            return True  # Cannot check yet
        return self.predicate(*values)


class UnaryConstraint(Constraint):
    """Constraint on a single variable."""

    def __init__(self, variable: str, predicate: Callable[[Any], bool]) -> None:
        """Initialize unary constraint.

        Args:
            variable: Variable name.
            predicate: Function taking single value.

        Example:
            >>> constraint = UnaryConstraint("width", lambda x: 0 < x < 100)
        """
        super().__init__([variable], predicate)
        self.variable = variable


class BinaryConstraint(Constraint):
    """Constraint on two variables."""

    def __init__(
        self,
        variable1: str,
        variable2: str,
        predicate: Callable[[Any, Any], bool],
    ) -> None:
        """Initialize binary constraint.

        Args:
            variable1: First variable name.
            variable2: Second variable name.
            predicate: Function taking two values.

        Example:
            >>> constraint = BinaryConstraint(
            ...     "inner_width",
            ...     "outer_width",
            ...     lambda inner, outer: inner < outer
            ... )
        """
        super().__init__([variable1, variable2], predicate)
        self.variable1 = variable1
        self.variable2 = variable2


class CSPSolver:
    """Constraint Satisfaction Problem solver using backtracking."""

    def __init__(self) -> None:
        """Initialize CSP solver."""
        self.variables: Set[str] = set()
        self.domains: Dict[str, List[Any]] = {}
        self.constraints: List[Constraint] = []

    def add_variable(self, name: str, domain: List[Any]) -> None:
        """Add a variable with its domain.

        Args:
            name: Variable name.
            domain: List of possible values.

        Example:
            >>> solver = CSPSolver()
            >>> solver.add_variable("size", [10, 12, 14, 16])
        """
        self.variables.add(name)
        self.domains[name] = domain

    def add_constraint(self, constraint: Constraint) -> None:
        """Add a constraint.

        Args:
            constraint: Constraint to add.
        """
        self.constraints.append(constraint)

    def is_consistent(
        self,
        variable: str,
        value: Any,
        assignment: Dict[str, Any],
    ) -> bool:
        """Check if assigning value to variable is consistent with constraints.

        Args:
            variable: Variable name.
            value: Value to assign.
            assignment: Current partial assignment.

        Returns:
            True if consistent with all constraints.
        """
        test_assignment = {**assignment, variable: value}

        for constraint in self.constraints:
            if variable in constraint.variables:
                if not constraint.is_satisfied(test_assignment):
                    return False

        return True

    def backtrack(
        self,
        assignment: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Backtracking search for solution.

        Args:
            assignment: Current partial assignment.

        Returns:
            Complete assignment if solution found, None otherwise.
        """
        # Check if assignment is complete
        if len(assignment) == len(self.variables):
            return assignment

        # Select unassigned variable
        unassigned = [v for v in self.variables if v not in assignment]
        if not unassigned:
            return None

        variable = unassigned[0]

        # Try each value in domain
        for value in self.domains[variable]:
            if self.is_consistent(variable, value, assignment):
                new_assignment = {**assignment, variable: value}
                result = self.backtrack(new_assignment)
                if result is not None:
                    return result

        return None

    def solve(self) -> Optional[Dict[str, Any]]:
        """Find a solution to the CSP.

        Returns:
            Variable -> value assignment if solution found, None otherwise.

        Example:
            >>> solver = CSPSolver()
            >>> solver.add_variable("x", [1, 2, 3])
            >>> solver.add_variable("y", [1, 2, 3])
            >>> solver.add_constraint(BinaryConstraint("x", "y", lambda x, y: x < y))
            >>> solution = solver.solve()
            >>> solution["x"] < solution["y"]
            True
        """
        return self.backtrack({})

    def find_all_solutions(self, max_solutions: int = 100) -> List[Dict[str, Any]]:
        """Find all solutions (or up to max).

        Args:
            max_solutions: Maximum number of solutions to find.

        Returns:
            List of solutions.
        """
        solutions: List[Dict[str, Any]] = []

        def backtrack_all(assignment: Dict[str, Any]) -> None:
            if len(solutions) >= max_solutions:
                return

            if len(assignment) == len(self.variables):
                solutions.append(assignment.copy())
                return

            unassigned = [v for v in self.variables if v not in assignment]
            if not unassigned:
                return

            variable = unassigned[0]

            for value in self.domains[variable]:
                if self.is_consistent(variable, value, assignment):
                    assignment[variable] = value
                    backtrack_all(assignment)
                    del assignment[variable]

        backtrack_all({})
        return solutions


class ConstraintPropagator:
    """Constraint propagation for domain reduction."""

    @staticmethod
    def arc_consistency(
        solver: CSPSolver,
    ) -> Tuple[bool, Dict[str, List[Any]]]:
        """Apply arc consistency (AC-3 algorithm).

        Args:
            solver: CSP solver with variables and constraints.

        Returns:
            Tuple of (is_consistent, reduced_domains).

        Example:
            >>> solver = CSPSolver()
            >>> solver.add_variable("x", [1, 2, 3, 4, 5])
            >>> solver.add_variable("y", [1, 2, 3, 4, 5])
            >>> solver.add_constraint(BinaryConstraint("x", "y", lambda x, y: x < y))
            >>> consistent, domains = ConstraintPropagator.arc_consistency(solver)
            >>> consistent
            True
        """
        domains = {var: list(domain) for var, domain in solver.domains.items()}

        # Create queue of arcs
        queue: List[Tuple[str, Constraint]] = []
        for constraint in solver.constraints:
            for variable in constraint.variables:
                queue.append((variable, constraint))

        while queue:
            variable, constraint = queue.pop(0)

            if _revise(variable, constraint, domains):
                if not domains[variable]:
                    return False, domains  # Domain wipe-out

                # Add neighbors back to queue
                for other_constraint in solver.constraints:
                    if variable in other_constraint.variables:
                        for neighbor in other_constraint.variables:
                            if neighbor != variable:
                                queue.append((neighbor, other_constraint))

        return True, domains


def _revise(
    variable: str,
    constraint: Constraint,
    domains: Dict[str, List[Any]],
) -> bool:
    """Revise domain of variable based on constraint.

    Returns:
        True if domain was revised.
    """
    revised = False
    to_remove = []

    for value in domains[variable]:
        # Check if there exists a consistent assignment
        test_assignment = {variable: value}

        # Try to find values for other variables
        satisfiable = False
        for other_var in constraint.variables:
            if other_var == variable:
                continue

            for other_value in domains[other_var]:
                test_assignment[other_var] = other_value
                if constraint.is_satisfied(test_assignment):
                    satisfiable = True
                    break

            if satisfiable:
                break

        if not satisfiable:
            to_remove.append(value)
            revised = True

    for value in to_remove:
        domains[variable].remove(value)

    return revised


class ParameterConstraintChecker:
    """High-level constraint checker for parameter sets."""

    @staticmethod
    def check_constraints(
        parameters: Dict[str, Parameter],
        values: Dict[str, Any],
    ) -> Tuple[bool, List[str]]:
        """Check if parameter values satisfy all constraints.

        Args:
            parameters: Parameter definitions.
            values: Parameter values to check.

        Returns:
            Tuple of (is_valid, error_messages).

        Example:
            >>> from koocad.core.parameters import FloatParameter
            >>> params = {
            ...     "width": FloatParameter(name="width", value=10, min_value=5, max_value=20)
            ... }
            >>> valid, errors = ParameterConstraintChecker.check_constraints(
            ...     params, {"width": 15}
            ... )
            >>> valid
            True
        """
        errors = []

        for name, param in parameters.items():
            value = values.get(name)
            if value is None:
                continue

            # Check parameter constraints
            for constraint in param.constraints:
                if not constraint.validate(value):
                    errors.append(
                        f"Parameter '{name}': {constraint.message} (value={value})"
                    )

        return len(errors) == 0, errors
