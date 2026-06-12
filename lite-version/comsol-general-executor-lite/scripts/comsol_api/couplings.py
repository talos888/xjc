from __future__ import annotations

from typing import Any
from jpype.types import JInt

from .utils import apply_selection, label_if_present, set_indexed_properties, set_properties


def build_couplings(java, plan: dict[str, Any]) -> None:
    for coupling in plan.get("couplings", []) or []:
        component_tag = str(coupling["component"])
        tag = str(coupling["tag"])
        api_type = str(coupling["api_type"])
        java.component(component_tag).cpl().create(tag, api_type)
        obj = java.component(component_tag).cpl(tag)
        label_if_present(obj, coupling)
        if "geometry" in coupling and "dimension" in coupling:
            obj.selection().geom(
                str(coupling["geometry"]), JInt(int(coupling["dimension"]))
            )
        apply_selection(obj, coupling.get("selection"))
        set_properties(obj, coupling.get("properties"))
        set_indexed_properties(obj, coupling.get("indexed_properties"))
