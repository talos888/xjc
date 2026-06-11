from __future__ import annotations

from typing import Any

from .utils import label_if_present, set_indexed_properties, set_properties


def build_exports(java, plan: dict[str, Any]) -> None:
    for export in plan.get("exports", []) or []:
        tag = str(export["tag"])
        java.result().export().create(tag, str(export["api_type"]))
        export_obj = java.result().export(tag)
        label_if_present(export_obj, export)
        set_properties(export_obj, export.get("properties"))
        set_indexed_properties(export_obj, export.get("indexed_properties"))
        if export.get("run", False):
            export_obj.run()
