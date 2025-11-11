"""
Parameter metadata and annotation system.

This module provides rich metadata support for parameters including
descriptions, tags, categories, and automatic documentation generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from koocad.core.parameters import ParameterSet


class ParameterCategory(Enum):
    """Standard parameter categories."""

    GEOMETRY = "geometry"
    MATERIAL = "material"
    MANUFACTURING = "manufacturing"
    ELECTRICAL = "electrical"
    THERMAL = "thermal"
    MECHANICAL = "mechanical"
    DESIGN_RULE = "design_rule"
    COST = "cost"
    OTHER = "other"


@dataclass
class ParameterMetadata:
    """Rich metadata for parameters."""

    # Basic information
    display_name: str = ""
    description: str = ""
    category: ParameterCategory = ParameterCategory.OTHER

    # Tags for search and filtering
    tags: set[str] = field(default_factory=set)

    # Documentation
    tooltip: str = ""
    help_url: str | None = None
    example_values: list[Any] = field(default_factory=list)

    # Provenance
    created_by: str | None = None
    created_at: datetime | None = None
    modified_by: str | None = None
    modified_at: datetime | None = None

    # Engineering context
    standard: str | None = None  # e.g., "JEDEC", "IPC-7351", "EIA"
    reference: str | None = None  # Document reference

    # UI hints
    ui_order: int = 0  # Display order in UI
    ui_group: str | None = None  # Group in UI
    ui_readonly: bool = False
    ui_hidden: bool = False

    # Validation hints
    warning_threshold: float | None = None
    critical_threshold: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category.value,
            "tags": list(self.tags),
            "tooltip": self.tooltip,
            "help_url": self.help_url,
            "example_values": self.example_values,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_by": self.modified_by,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
            "standard": self.standard,
            "reference": self.reference,
            "ui_order": self.ui_order,
            "ui_group": self.ui_group,
            "ui_readonly": self.ui_readonly,
            "ui_hidden": self.ui_hidden,
            "warning_threshold": self.warning_threshold,
            "critical_threshold": self.critical_threshold,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> ParameterMetadata:
        """Create metadata from dictionary."""
        return ParameterMetadata(
            display_name=data.get("display_name", ""),
            description=data.get("description", ""),
            category=ParameterCategory(data.get("category", "other")),
            tags=set(data.get("tags", [])),
            tooltip=data.get("tooltip", ""),
            help_url=data.get("help_url"),
            example_values=data.get("example_values", []),
            created_by=data.get("created_by"),
            created_at=(
                datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
            ),
            modified_by=data.get("modified_by"),
            modified_at=(
                datetime.fromisoformat(data["modified_at"]) if data.get("modified_at") else None
            ),
            standard=data.get("standard"),
            reference=data.get("reference"),
            ui_order=data.get("ui_order", 0),
            ui_group=data.get("ui_group"),
            ui_readonly=data.get("ui_readonly", False),
            ui_hidden=data.get("ui_hidden", False),
            warning_threshold=data.get("warning_threshold"),
            critical_threshold=data.get("critical_threshold"),
        )


class MetadataRegistry:
    """Registry for parameter metadata."""

    def __init__(self) -> None:
        """Initialize metadata registry."""
        self.metadata: dict[str, ParameterMetadata] = {}

    def register(self, param_name: str, metadata: ParameterMetadata) -> None:
        """Register metadata for parameter.

        Args:
            param_name: Parameter name.
            metadata: Metadata to register.
        """
        self.metadata[param_name] = metadata

    def get(self, param_name: str) -> ParameterMetadata | None:
        """Get metadata for parameter.

        Args:
            param_name: Parameter name.

        Returns:
            Metadata if found, None otherwise.
        """
        return self.metadata.get(param_name)

    def search_by_tag(self, tag: str) -> list[str]:
        """Search parameters by tag.

        Args:
            tag: Tag to search for.

        Returns:
            List of parameter names with matching tag.
        """
        return [name for name, meta in self.metadata.items() if tag in meta.tags]

    def search_by_category(self, category: ParameterCategory) -> list[str]:
        """Search parameters by category.

        Args:
            category: Category to search for.

        Returns:
            List of parameter names in category.
        """
        return [name for name, meta in self.metadata.items() if meta.category == category]

    def search_by_text(self, query: str) -> list[str]:
        """Full-text search in metadata.

        Args:
            query: Search query.

        Returns:
            List of parameter names matching query.
        """
        query_lower = query.lower()
        results = []

        for name, meta in self.metadata.items():
            # Search in name, display_name, description, tooltip
            searchable_text = " ".join(
                [
                    name,
                    meta.display_name,
                    meta.description,
                    meta.tooltip,
                ]
            ).lower()

            if query_lower in searchable_text:
                results.append(name)

        return results

    def get_ui_groups(self) -> dict[str, list[str]]:
        """Get parameters organized by UI group.

        Returns:
            Dictionary mapping group names to parameter names.
        """
        groups: dict[str, list[str]] = {}

        for name, meta in self.metadata.items():
            group = meta.ui_group or "General"
            if group not in groups:
                groups[group] = []
            groups[group].append(name)

        # Sort by ui_order within each group
        for group in groups:
            groups[group].sort(key=lambda n: self.metadata[n].ui_order)

        return groups


class DocumentationGenerator:
    """Automatic documentation generation from parameter metadata."""

    @staticmethod
    def generate_markdown(
        param_set: ParameterSet,
        registry: MetadataRegistry,
        title: str = "Parameter Documentation",
    ) -> str:
        """Generate Markdown documentation.

        Args:
            param_set: ParameterSet to document.
            registry: Metadata registry.
            title: Document title.

        Returns:
            Markdown string.
        """
        lines = [
            f"# {title}",
            "",
            f"*Generated: {datetime.now().isoformat()}*",
            "",
            "---",
            "",
        ]

        # Group by category
        categories: dict[ParameterCategory, list[str]] = {}
        for name in param_set.parameters.keys():
            meta = registry.get(name)
            category = meta.category if meta else ParameterCategory.OTHER
            if category not in categories:
                categories[category] = []
            categories[category].append(name)

        # Generate documentation for each category
        for category, param_names in sorted(categories.items(), key=lambda x: x[0].value):
            lines.append(f"## {category.value.title()} Parameters")
            lines.append("")

            for param_name in sorted(param_names):
                param = param_set.get(param_name)
                meta = registry.get(param_name)

                if param is None:
                    continue

                # Parameter name and type
                display_name = meta.display_name if meta and meta.display_name else param_name
                lines.append(f"### {display_name}")
                lines.append("")
                lines.append(f"**Name:** `{param_name}`")
                lines.append(f"**Type:** `{param.__class__.__name__}`")
                lines.append(f"**Default Value:** `{param.value}`")
                lines.append("")

                # Description
                if meta and meta.description:
                    lines.append(meta.description)
                    lines.append("")

                # Additional metadata
                if meta:
                    if meta.tags:
                        lines.append(f"**Tags:** {', '.join(sorted(meta.tags))}")
                        lines.append("")

                    if meta.standard:
                        lines.append(f"**Standard:** {meta.standard}")
                        if meta.reference:
                            lines.append(f"**Reference:** {meta.reference}")
                        lines.append("")

                    if meta.example_values:
                        lines.append("**Example Values:**")
                        for example in meta.example_values:
                            lines.append(f"- `{example}`")
                        lines.append("")

                    if meta.help_url:
                        lines.append(f"**More Info:** {meta.help_url}")
                        lines.append("")

                lines.append("---")
                lines.append("")

        return "\n".join(lines)

    @staticmethod
    def generate_html(
        param_set: ParameterSet,
        registry: MetadataRegistry,
        title: str = "Parameter Documentation",
    ) -> str:
        """Generate HTML documentation.

        Args:
            param_set: ParameterSet to document.
            registry: Metadata registry.
            title: Document title.

        Returns:
            HTML string.
        """
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<title>{title}</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }",
            "h1 { color: #333; }",
            "h2 { color: #666; border-bottom: 2px solid #ddd; padding-bottom: 5px; }",
            "h3 { color: #999; }",
            ".param { margin-bottom: 30px; padding: 15px; background: #f9f9f9; border-left: 4px solid #4CAF50; }",
            ".meta { color: #666; font-size: 0.9em; }",
            ".tag { display: inline-block; background: #e0e0e0; padding: 2px 8px; margin: 2px; border-radius: 3px; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{title}</h1>",
            f"<p class='meta'>Generated: {datetime.now().isoformat()}</p>",
        ]

        # Group by category
        categories: dict[ParameterCategory, list[str]] = {}
        for name in param_set.parameters.keys():
            meta = registry.get(name)
            category = meta.category if meta else ParameterCategory.OTHER
            if category not in categories:
                categories[category] = []
            categories[category].append(name)

        # Generate HTML for each category
        for category, param_names in sorted(categories.items(), key=lambda x: x[0].value):
            html_parts.append(f"<h2>{category.value.title()} Parameters</h2>")

            for param_name in sorted(param_names):
                param = param_set.get(param_name)
                meta = registry.get(param_name)

                if param is None:
                    continue

                html_parts.append("<div class='param'>")

                display_name = meta.display_name if meta and meta.display_name else param_name
                html_parts.append(f"<h3>{display_name}</h3>")
                html_parts.append(
                    f"<p class='meta'><strong>Name:</strong> <code>{param_name}</code></p>"
                )
                html_parts.append(
                    f"<p class='meta'><strong>Type:</strong> <code>{param.__class__.__name__}</code></p>"
                )
                html_parts.append(
                    f"<p class='meta'><strong>Default:</strong> <code>{param.value}</code></p>"
                )

                if meta and meta.description:
                    html_parts.append(f"<p>{meta.description}</p>")

                if meta and meta.tags:
                    html_parts.append("<p>")
                    for tag in sorted(meta.tags):
                        html_parts.append(f"<span class='tag'>{tag}</span>")
                    html_parts.append("</p>")

                html_parts.append("</div>")

        html_parts.extend(["</body>", "</html>"])

        return "\n".join(html_parts)
