from __future__ import annotations

from typing import Any
from jpype.types import JInt

from .utils import apply_selection, label_if_present, set_indexed_properties, set_properties


def boundary_dimension(plan: dict[str, Any], component_tag: str, spec: dict[str, Any]) -> int:
    if "dimension" in spec:
        return int(spec["dimension"])
    for component in plan.get("components", []) or []:
        if str(component.get("tag", "comp1")) == component_tag:
            return max(0, int(component.get("dimension", 2)) - 1)
    raise ValueError(
        f"Cannot infer boundary dimension for component {component_tag}; "
        "add the component or set dimension explicitly."
    )


def build_wave_optics_helpers(java, plan: dict[str, Any]) -> None:
    """Create optional helper features for Wave Optics plans.

    These helpers still use COMSOL Java API types from the plan. They do not
    infer physics from literature; they only reduce repeated feature wiring.
    """
    for port in plan.get("ports", []) or []:
        component_tag = str(port["component"])
        physics_tag = str(port["physics"])
        tag = str(port["tag"])
        interface = java.component(component_tag).physics(physics_tag)
        interface.create(
            tag,
            str(port.get("api_type", "Port")),
            JInt(boundary_dimension(plan, component_tag, port)),
        )
        feature = interface.feature(tag)
        label_if_present(feature, port)
        apply_selection(feature, port.get("selection"))
        set_properties(feature, port.get("properties"))
        set_indexed_properties(feature, port.get("indexed_properties"))

    for boundary in plan.get("scattering_boundaries", []) or []:
        component_tag = str(boundary["component"])
        physics_tag = str(boundary["physics"])
        tag = str(boundary["tag"])
        interface = java.component(component_tag).physics(physics_tag)
        interface.create(
            tag,
            str(boundary.get("api_type", "Scattering")),
            JInt(boundary_dimension(plan, component_tag, boundary)),
        )
        feature = interface.feature(tag)
        label_if_present(feature, boundary)
        apply_selection(feature, boundary.get("selection"))
        set_properties(feature, boundary.get("properties"))
        set_indexed_properties(feature, boundary.get("indexed_properties"))

    for pml in plan.get("pml", []) or []:
        component_tag = str(pml["component"])
        coord_tag = str(pml["tag"])
        component = java.component(component_tag)
        component.coordSystem().create(coord_tag, str(pml.get("api_type", "PML")))
        coord = component.coordSystem(coord_tag)
        label_if_present(coord, pml)
        apply_selection(coord, pml.get("selection"))
        set_properties(coord, pml.get("properties"))
        set_indexed_properties(coord, pml.get("indexed_properties"))
