"""
Node-based visual editor for parametric CAD.

This module provides a node editor interface where users can
create parametric designs by connecting nodes.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Callable

try:
    import dearpygui.dearpygui as dpg
except ImportError:
    dpg = None  # type: ignore

from koocad.ui.graph_executor import GraphExecutor


class Node:
    """Base class for nodes in the node editor."""

    def __init__(self, node_id: int, label: str, pos: tuple[int, int] = (0, 0)) -> None:
        """Initialize node.

        Args:
            node_id: Unique node ID.
            label: Node label.
            pos: Initial position (x, y).
        """
        self.node_id = node_id
        self.label = label
        self.pos = pos
        self.inputs: List[int] = []
        self.outputs: List[int] = []
        self.parameters: Dict[str, Any] = {}

    def create(self, parent: int) -> None:
        """Create node in DearPyGui.

        Args:
            parent: Parent node editor ID.
        """
        with dpg.node(label=self.label, parent=parent, tag=self.node_id, pos=self.pos):
            # Create input pins
            for i, input_name in enumerate(self.get_inputs()):
                pin_id = self.node_id * 1000 + i
                dpg.add_node_attribute(
                    label=input_name,
                    attribute_type=dpg.mvNode_Attr_Input,
                    tag=pin_id,
                )
                self.inputs.append(pin_id)

            # Create parameter controls
            self.create_parameters()

            # Create output pins
            for i, output_name in enumerate(self.get_outputs()):
                pin_id = self.node_id * 1000 + 100 + i
                dpg.add_node_attribute(
                    label=output_name,
                    attribute_type=dpg.mvNode_Attr_Output,
                    tag=pin_id,
                )
                self.outputs.append(pin_id)

    def get_inputs(self) -> List[str]:
        """Get list of input pin names."""
        return []

    def get_outputs(self) -> List[str]:
        """Get list of output pin names."""
        return ["Output"]

    def create_parameters(self) -> None:
        """Create parameter controls in node."""
        pass

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute node computation.

        Args:
            inputs: Dictionary of input values.

        Returns:
            Dictionary of output values.
        """
        return {}


class ParameterNode(Node):
    """Node for inputting parameter values."""

    def __init__(self, node_id: int, param_name: str, param_type: str = "float", default_value: Any = 0.0):
        """Initialize parameter node.

        Args:
            node_id: Unique node ID.
            param_name: Parameter name.
            param_type: Parameter type ("float", "int", "string").
            default_value: Default parameter value.
        """
        super().__init__(node_id, f"Parameter: {param_name}")
        self.param_name = param_name
        self.param_type = param_type
        self.parameters["value"] = default_value

    def get_outputs(self) -> List[str]:
        """Parameter node has one output."""
        return [self.param_name]

    def create_parameters(self) -> None:
        """Create parameter input control."""
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
            if self.param_type == "float":
                dpg.add_input_float(
                    label="",
                    default_value=self.parameters["value"],
                    callback=lambda s, v: self.parameters.update({"value": v}),
                    width=150,
                )
            elif self.param_type == "int":
                dpg.add_input_int(
                    label="",
                    default_value=self.parameters["value"],
                    callback=lambda s, v: self.parameters.update({"value": v}),
                    width=150,
                )
            elif self.param_type == "string":
                dpg.add_input_text(
                    label="",
                    default_value=str(self.parameters["value"]),
                    callback=lambda s, v: self.parameters.update({"value": v}),
                    width=150,
                )

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute parameter node to output its value.

        Args:
            inputs: Unused for parameter nodes.

        Returns:
            Dictionary with parameter name as key and value.
        """
        return {self.param_name: self.parameters["value"]}


class ComponentNode(Node):
    """Node for electronic component generation."""

    def __init__(self, node_id: int, component_type: str):
        """Initialize component node.

        Args:
            node_id: Unique node ID.
            component_type: Type of component (BGA, MLCC, etc.).
        """
        super().__init__(node_id, component_type)
        self.component_type = component_type
        self._setup_default_parameters()
        self.generator = None  # Will hold the actual generator instance

    def _setup_default_parameters(self) -> None:
        """Setup default parameters based on component type."""
        if self.component_type == "BGA":
            self.parameters = {
                "substrate_width": 12.0,
                "substrate_height": 12.0,
                "substrate_thickness": 0.8,
                "ball_rows": 15,
                "ball_cols": 15,
                "ball_pitch": 0.8,
                "ball_diameter": 0.4,
            }
        elif self.component_type == "MLCC":
            self.parameters = {
                "body_length": 2.0,
                "body_width": 1.25,
                "body_height": 1.25,
                "termination_length": 0.25,
            }
        elif self.component_type == "Resistor":
            self.parameters = {
                "body_length": 2.0,
                "body_width": 1.25,
                "body_height": 0.6,
                "termination_length": 0.25,
            }
        else:
            self.parameters = {}

    def get_inputs(self) -> List[str]:
        """Component nodes can receive parameter inputs."""
        return list(self.parameters.keys())

    def get_outputs(self) -> List[str]:
        """Component nodes output a shape."""
        return ["Shape"]

    def create_parameters(self) -> None:
        """Create parameter controls."""
        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
            dpg.add_text(f"{self.component_type} Parameters:")

            # Create slider/input for each parameter
            for param_name, default_value in self.parameters.items():
                if isinstance(default_value, float):
                    dpg.add_slider_float(
                        label=param_name,
                        default_value=default_value,
                        min_value=0.0,
                        max_value=50.0,
                        callback=lambda s, v, u: self.parameters.update({u: v}),
                        user_data=param_name,
                        width=150,
                    )
                elif isinstance(default_value, int):
                    dpg.add_slider_int(
                        label=param_name,
                        default_value=default_value,
                        min_value=1,
                        max_value=100,
                        callback=lambda s, v, u: self.parameters.update({u: v}),
                        user_data=param_name,
                        width=150,
                    )

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute node to generate component.

        Args:
            inputs: Dictionary of input values from connected nodes.

        Returns:
            Dictionary with 'Shape' key containing generated shape.
        """
        # Merge inputs with node's parameters (inputs override parameters)
        params = self.parameters.copy()
        params.update(inputs)

        try:
            # Try to import and create generator
            # This is a simplified version - in production would use proper factory
            if self.component_type == "BGA":
                from koocad.generators.bga import BGAGenerator
                gen = BGAGenerator(
                    substrate_width=params.get("substrate_width", 12.0),
                    substrate_height=params.get("substrate_height", 12.0),
                    substrate_thickness=params.get("substrate_thickness", 0.8),
                    ball_rows=params.get("ball_rows", 15),
                    ball_cols=params.get("ball_cols", 15),
                    ball_pitch=params.get("ball_pitch", 0.8),
                    ball_diameter=params.get("ball_diameter", 0.4),
                )
            elif self.component_type == "MLCC":
                from koocad.generators.passives import MLCCGenerator
                gen = MLCCGenerator(
                    body_length=params.get("body_length", 2.0),
                    body_width=params.get("body_width", 1.25),
                    body_height=params.get("body_height", 1.25),
                    termination_length=params.get("termination_length", 0.25),
                )
            elif self.component_type == "Resistor":
                from koocad.generators.passives import ChipResistorGenerator
                gen = ChipResistorGenerator(
                    body_length=params.get("body_length", 2.0),
                    body_width=params.get("body_width", 1.25),
                    body_height=params.get("body_height", 0.6),
                    termination_length=params.get("termination_length", 0.25),
                )
            else:
                # Unsupported component type
                print(f"Component type {self.component_type} not yet implemented")
                return {"Shape": None}

            # Generate the shape
            shape = gen.generate()
            return {"Shape": shape}

        except ImportError as e:
            print(f"Cannot generate {self.component_type}: {e}")
            print("Note: CadQuery must be installed for actual shape generation")
            return {"Shape": None}
        except Exception as e:
            print(f"Error generating {self.component_type}: {e}")
            return {"Shape": None}


class NodeEditor:
    """Node editor for visual programming."""

    def __init__(self) -> None:
        """Initialize node editor."""
        if dpg is None:
            raise ImportError("DearPyGui is required")

        self.editor_id = dpg.generate_uuid()
        self.nodes: Dict[int, Node] = {}
        self.links: List[tuple[int, int]] = []
        self.next_node_id = 1
        self.executor = GraphExecutor()
        self.execution_callback: Optional[Callable[[Any], None]] = None

    def create(self) -> None:
        """Create node editor widget."""
        with dpg.node_editor(
            tag=self.editor_id,
            callback=self.on_link_created,
            delink_callback=self.on_link_deleted,
        ):
            pass

    def add_node(self, node: Node) -> None:
        """Add node to editor.

        Args:
            node: Node to add.
        """
        self.nodes[node.node_id] = node
        node.create(self.editor_id)

    def add_parameter_node(self, param_name: str, param_type: str = "float", default_value: Any = 0.0) -> None:
        """Add parameter input node.

        Args:
            param_name: Parameter name.
            param_type: Parameter type.
            default_value: Default value.
        """
        node_id = self.next_node_id
        self.next_node_id += 1

        node = ParameterNode(node_id, param_name, param_type, default_value)
        self.add_node(node)

    def add_component_node(self, component_type: str) -> None:
        """Add component generation node.

        Args:
            component_type: Type of component to add.
        """
        node_id = self.next_node_id
        self.next_node_id += 1

        node = ComponentNode(node_id, component_type)
        self.add_node(node)

    def on_link_created(self, sender: int, app_data: tuple) -> None:
        """Callback when link is created.

        Args:
            sender: Sender ID.
            app_data: Tuple of (from_pin, to_pin).
        """
        from_pin, to_pin = app_data
        self.links.append((from_pin, to_pin))
        print(f"Link created: {from_pin} -> {to_pin}")

    def on_link_deleted(self, sender: int, app_data: int) -> None:
        """Callback when link is deleted.

        Args:
            sender: Sender ID.
            app_data: Link ID.
        """
        print(f"Link deleted: {app_data}")
        # Remove link from list
        self.links = [(f, t) for f, t in self.links if not (f == app_data or t == app_data)]

    def delete_selected(self) -> None:
        """Delete selected nodes."""
        selected = dpg.get_selected_nodes(self.editor_id)
        for node_id in selected:
            if node_id in self.nodes:
                dpg.delete_item(node_id)
                del self.nodes[node_id]

    def clear(self) -> None:
        """Clear all nodes and links."""
        for node_id in list(self.nodes.keys()):
            dpg.delete_item(node_id)

        self.nodes.clear()
        self.links.clear()
        self.next_node_id = 1

    def execute_graph(self) -> Optional[Any]:
        """Execute node graph to generate CAD model.

        Returns:
            The result from the final output node, or None if execution fails.
        """
        if not self.nodes:
            print("No nodes to execute")
            return None

        # Execute graph using executor
        results = self.executor.execute_graph(self.nodes, self.links)

        if not results:
            print("Graph execution failed - check for cycles or errors")
            return None

        # Find output nodes (nodes with no outgoing connections)
        output_nodes = []
        for node_id in self.nodes.keys():
            has_output = any(from_pin // 1000 == node_id for from_pin, _ in self.links)
            if not has_output:
                output_nodes.append(node_id)

        # Get result from the last output node
        final_result = None
        for node_id in output_nodes:
            if node_id in results and results[node_id].success:
                final_result = results[node_id].outputs.get("Output") or results[node_id].outputs.get("Shape")

        # Call callback if registered
        if self.execution_callback and final_result:
            self.execution_callback(final_result)

        print(f"Graph executed successfully. {len(results)} nodes processed.")
        return final_result
