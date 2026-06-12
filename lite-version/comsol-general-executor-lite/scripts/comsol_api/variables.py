from __future__ import annotations

from typing import Any

from .utils import apply_selection, label_if_present, set_indexed_properties, set_properties


def build_variables(java, plan: dict[str, Any]) -> None:
    for variable in plan.get("variables", []) or []:
        component_tag = variable.get("component")
        tag = str(variable["tag"])
        if component_tag:
            component = java.component(str(component_tag))
            component.variable().create(tag)
            var_obj = component.variable(tag)
        else:
            java.variable().create(tag)
            var_obj = java.variable(tag)
        label_if_present(var_obj, variable)
        apply_selection(var_obj, variable.get("selection"))
        for name, expression in variable.get("expressions", {}).items():
            var_obj.set(str(name), str(expression))
        set_properties(var_obj, variable.get("properties"))
        set_indexed_properties(var_obj, variable.get("indexed_properties"))
