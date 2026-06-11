from __future__ import annotations

from typing import Any


def comsol_value(value: Any) -> Any:
    if isinstance(value, dict):
        if "$bool" in value:
            return bool(value["$bool"])
        if "$int" in value:
            from jpype.types import JInt

            return JInt(int(value["$int"]))
        if "$double" in value:
            from jpype.types import JDouble

            return JDouble(float(value["$double"]))
        if "$string" in value:
            return str(value["$string"])
        if "$int_array" in value:
            from jpype import JArray
            from jpype.types import JInt

            return JArray(JInt)([int(item) for item in value["$int_array"]])
        if "$string_array" in value:
            return [str(item) for item in value["$string_array"]]
        raise ValueError(f"Unknown typed COMSOL value: {value}")
    if isinstance(value, bool):
        return "on" if value else "off"
    return str(value)


def set_properties(feature, properties: dict[str, Any] | None) -> None:
    for key, value in (properties or {}).items():
        if isinstance(value, list):
            feature.set(str(key), [comsol_value(item) for item in value])
        else:
            feature.set(str(key), comsol_value(value))


def set_indexed_properties(feature, indexed_properties: list[dict[str, Any]] | None) -> None:
    for item in indexed_properties or []:
        key = str(item["property"])
        value = item["value"]
        index = int(item["index"])
        if "outer_index" in item:
            feature.setIndex(key, comsol_value(value), index, int(item["outer_index"]))
        else:
            feature.setIndex(key, comsol_value(value), index)


def set_property_groups(feature, property_groups: list[dict[str, Any]] | None) -> None:
    for group in property_groups or []:
        group_tag = str(group.get("group") or group.get("tag"))
        prop = feature.prop(group_tag)
        set_properties(prop, group.get("properties"))
        set_indexed_properties(prop, group.get("indexed_properties"))


def apply_selection(feature, selection: Any) -> None:
    if selection is None:
        return
    selector = feature.selection()
    if selection == "all":
        selector.all()
        return
    if isinstance(selection, dict):
        if selection.get("all"):
            selector.all()
            return
        if "named" in selection:
            selector.named(str(selection["named"]))
            return
        if "entities" in selection:
            selector.set(selection["entities"])
            return
    selector.set(selection)


def apply_named_selections(feature, selections: dict[str, Any] | None) -> None:
    for slot, selection in (selections or {}).items():
        selector = feature.selection(str(slot))
        if isinstance(selection, dict) and "named" in selection:
            selector.named(str(selection["named"]))
        elif isinstance(selection, dict) and selection.get("all"):
            selector.all()
        elif isinstance(selection, dict) and "entities" in selection:
            selector.set(selection["entities"])
        else:
            selector.set(selection)


def label_if_present(feature, spec: dict[str, Any]) -> None:
    if "label" in spec:
        feature.label(str(spec["label"]))
