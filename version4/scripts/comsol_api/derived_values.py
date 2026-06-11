from __future__ import annotations

from typing import Any

from .utils import apply_selection, label_if_present, set_indexed_properties, set_properties


def build_derived_values(java, plan: dict[str, Any]) -> None:
    for value in plan.get("derived_values", []) or []:
        tag = str(value["tag"])
        api_type = str(value["api_type"])
        java.result().numerical().create(tag, api_type)
        numerical = java.result().numerical(tag)
        label_if_present(numerical, value)
        apply_selection(numerical, value.get("selection"))
        set_properties(numerical, value.get("properties"))
        set_indexed_properties(numerical, value.get("indexed_properties"))
        if "table" in value:
            numerical.set("table", str(value["table"]))
        if value.get("evaluate", False):
            numerical.setResult()
