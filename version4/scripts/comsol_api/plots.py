from __future__ import annotations

from typing import Any

from .utils import label_if_present, set_indexed_properties, set_properties


def build_plots(java, plan: dict[str, Any]) -> None:
    for plot in plan.get("plots", []) or plan.get("results", []) or []:
        tag = str(plot["tag"])
        java.result().create(tag, str(plot["api_type"]))
        plot_group = java.result(tag)
        label_if_present(plot_group, plot)
        set_properties(plot_group, plot.get("properties"))
        set_indexed_properties(plot_group, plot.get("indexed_properties"))
        for feature in plot.get("features", []) or []:
            feature_tag = str(feature["tag"])
            plot_group.feature().create(feature_tag, str(feature["api_type"]))
            feature_obj = plot_group.feature(feature_tag)
            label_if_present(feature_obj, feature)
            set_properties(feature_obj, feature.get("properties"))
            set_indexed_properties(feature_obj, feature.get("indexed_properties"))
        if plot.get("run", True):
            plot_group.run()


def build_result_tables(java, plan: dict[str, Any]) -> None:
    for table in plan.get("tables", []) or []:
        tag = str(table["tag"])
        java.result().table().create(tag, str(table.get("api_type", "Table")))
        table_obj = java.result().table(tag)
        label_if_present(table_obj, table)
        set_properties(table_obj, table.get("properties"))
        set_indexed_properties(table_obj, table.get("indexed_properties"))


def build_numerical_results(java, plan: dict[str, Any]) -> None:
    for item in plan.get("numerical_results", []) or []:
        tag = str(item["tag"])
        java.result().numerical().create(tag, str(item["api_type"]))
        obj = java.result().numerical(tag)
        label_if_present(obj, item)
        set_properties(obj, item.get("properties"))
        set_indexed_properties(obj, item.get("indexed_properties"))
        if item.get("set_result"):
            obj.setResult()
