"""
History and Undo/Redo functionality for parameter changes.

This module implements the Command Pattern for undoable parameter operations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from koocad.core.parameters import Parameter, ParameterSet


class Command(ABC):
    """Base class for undoable commands."""

    def __init__(self) -> None:
        """Initialize command."""
        self.timestamp = datetime.now()

    @abstractmethod
    def execute(self) -> Any:
        """Execute the command."""
        ...

    @abstractmethod
    def undo(self) -> Any:
        """Undo the command."""
        ...

    @abstractmethod
    def redo(self) -> Any:
        """Redo the command (default: call execute)."""
        return self.execute()

    @abstractmethod
    def description(self) -> str:
        """Get human-readable description."""
        ...


class SetParameterValueCommand(Command):
    """Command to set a parameter value."""

    def __init__(
        self,
        param_set: ParameterSet,
        param_name: str,
        new_value: Any,
    ) -> None:
        """Initialize command.

        Args:
            param_set: Parameter set to modify.
            param_name: Parameter name.
            new_value: New value to set.
        """
        super().__init__()
        self.param_set = param_set
        self.param_name = param_name
        self.new_value = new_value
        self.old_value: Any | None = None

    def execute(self) -> None:
        """Execute command."""
        param = self.param_set.get(self.param_name)
        if param is None:
            raise KeyError(f"Parameter '{self.param_name}' not found")

        self.old_value = param.value
        param.value = self.new_value

    def undo(self) -> None:
        """Undo command."""
        if self.old_value is None:
            raise RuntimeError("Cannot undo: command was not executed")

        param = self.param_set.get(self.param_name)
        if param is not None:
            param.value = self.old_value

    def redo(self) -> None:
        """Redo command."""
        param = self.param_set.get(self.param_name)
        if param is not None:
            param.value = self.new_value

    def description(self) -> str:
        """Get description."""
        return f"Set {self.param_name} = {self.new_value}"


class AddParameterCommand(Command):
    """Command to add a new parameter."""

    def __init__(self, param_set: ParameterSet, parameter: Parameter) -> None:
        """Initialize command."""
        super().__init__()
        self.param_set = param_set
        self.parameter = parameter

    def execute(self) -> None:
        """Execute command."""
        self.param_set.add(self.parameter)

    def undo(self) -> None:
        """Undo command."""
        if self.parameter.name in self.param_set.parameters:
            del self.param_set.parameters[self.parameter.name]

    def description(self) -> str:
        """Get description."""
        return f"Add parameter {self.parameter.name}"


class RemoveParameterCommand(Command):
    """Command to remove a parameter."""

    def __init__(self, param_set: ParameterSet, param_name: str) -> None:
        """Initialize command."""
        super().__init__()
        self.param_set = param_set
        self.param_name = param_name
        self.removed_parameter: Parameter | None = None

    def execute(self) -> None:
        """Execute command."""
        self.removed_parameter = self.param_set.get(self.param_name)
        if self.removed_parameter is None:
            raise KeyError(f"Parameter '{self.param_name}' not found")

        del self.param_set.parameters[self.param_name]

    def undo(self) -> None:
        """Undo command."""
        if self.removed_parameter is None:
            raise RuntimeError("Cannot undo: command was not executed")

        self.param_set.add(self.removed_parameter)

    def description(self) -> str:
        """Get description."""
        return f"Remove parameter {self.param_name}"


class History:
    """Command history for undo/redo functionality."""

    def __init__(self, max_size: int = 100) -> None:
        """Initialize history.

        Args:
            max_size: Maximum number of commands to store.
        """
        self.max_size = max_size
        self.commands: list[Command] = []
        self.current_index: int = -1

    def execute(self, command: Command) -> None:
        """Execute a command and add to history.

        Args:
            command: Command to execute.

        Example:
            >>> history = History()
            >>> cmd = SetParameterValueCommand(params, "width", 15.0)
            >>> history.execute(cmd)
        """
        # Remove any commands after current index (discarding redo history)
        if self.current_index < len(self.commands) - 1:
            self.commands = self.commands[: self.current_index + 1]

        # Execute command
        command.execute()

        # Add to history
        self.commands.append(command)
        self.current_index += 1

        # Enforce max size
        if len(self.commands) > self.max_size:
            self.commands.pop(0)
            self.current_index -= 1

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return self.current_index >= 0

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return self.current_index < len(self.commands) - 1

    def undo(self) -> str | None:
        """Undo last command.

        Returns:
            Description of undone command, or None if nothing to undo.

        Example:
            >>> description = history.undo()
            >>> print(description)
            'Set width = 15.0'
        """
        if not self.can_undo():
            return None

        command = self.commands[self.current_index]
        command.undo()
        self.current_index -= 1

        return command.description()

    def redo(self) -> str | None:
        """Redo next command.

        Returns:
            Description of redone command, or None if nothing to redo.
        """
        if not self.can_redo():
            return None

        self.current_index += 1
        command = self.commands[self.current_index]
        command.redo()

        return command.description()

    def get_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent command history.

        Args:
            limit: Maximum number of commands to return.

        Returns:
            List of command information dictionaries.
        """
        start_idx = max(0, self.current_index - limit + 1)
        end_idx = self.current_index + 1

        history_items = []
        for i in range(start_idx, end_idx):
            cmd = self.commands[i]
            history_items.append(
                {
                    "index": i,
                    "description": cmd.description(),
                    "timestamp": cmd.timestamp.isoformat(),
                    "is_current": i == self.current_index,
                }
            )

        return history_items

    def clear(self) -> None:
        """Clear all history."""
        self.commands.clear()
        self.current_index = -1


@dataclass
class Snapshot:
    """Snapshot of parameter set state."""

    timestamp: datetime
    parameters: dict[str, Any]
    version: int
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "parameters": self.parameters,
            "version": self.version,
            "description": self.description,
        }


class SnapshotManager:
    """Manage parameter set snapshots for versioning."""

    def __init__(self) -> None:
        """Initialize snapshot manager."""
        self.snapshots: list[Snapshot] = []

    def take_snapshot(
        self,
        param_set: ParameterSet,
        description: str = "",
    ) -> Snapshot:
        """Take a snapshot of current parameter state.

        Args:
            param_set: Parameter set to snapshot.
            description: Optional description.

        Returns:
            Created snapshot.

        Example:
            >>> manager = SnapshotManager()
            >>> snapshot = manager.take_snapshot(params, "Before optimization")
        """
        snapshot = Snapshot(
            timestamp=datetime.now(),
            parameters={name: param.value for name, param in param_set.parameters.items()},
            version=len(self.snapshots) + 1,
            description=description,
        )

        self.snapshots.append(snapshot)
        return snapshot

    def restore_snapshot(
        self,
        param_set: ParameterSet,
        snapshot_index: int,
    ) -> None:
        """Restore parameter set from snapshot.

        Args:
            param_set: Parameter set to restore to.
            snapshot_index: Index of snapshot to restore (0-based).

        Example:
            >>> manager.restore_snapshot(params, 0)  # Restore to first snapshot
        """
        if snapshot_index < 0 or snapshot_index >= len(self.snapshots):
            raise IndexError(f"Snapshot index {snapshot_index} out of range")

        snapshot = self.snapshots[snapshot_index]

        for name, value in snapshot.parameters.items():
            param = param_set.get(name)
            if param is not None:
                param.value = value

    def get_latest_snapshot(self) -> Snapshot | None:
        """Get most recent snapshot."""
        return self.snapshots[-1] if self.snapshots else None

    def list_snapshots(self) -> list[dict[str, Any]]:
        """List all snapshots.

        Returns:
            List of snapshot information dictionaries.
        """
        return [
            {
                "index": i,
                "timestamp": snap.timestamp.isoformat(),
                "version": snap.version,
                "description": snap.description,
            }
            for i, snap in enumerate(self.snapshots)
        ]

    def diff_snapshots(
        self,
        snapshot1_index: int,
        snapshot2_index: int,
    ) -> dict[str, tuple[Any, Any]]:
        """Compute diff between two snapshots.

        Args:
            snapshot1_index: First snapshot index.
            snapshot2_index: Second snapshot index.

        Returns:
            Dictionary of parameter_name -> (old_value, new_value).

        Example:
            >>> diff = manager.diff_snapshots(0, 1)
            >>> for param, (old, new) in diff.items():
            ...     print(f"{param}: {old} → {new}")
        """
        snap1 = self.snapshots[snapshot1_index]
        snap2 = self.snapshots[snapshot2_index]

        diff: dict[str, tuple[Any, Any]] = {}

        all_params = set(snap1.parameters.keys()) | set(snap2.parameters.keys())

        for param in all_params:
            val1 = snap1.parameters.get(param)
            val2 = snap2.parameters.get(param)

            if val1 != val2:
                diff[param] = (val1, val2)

        return diff
