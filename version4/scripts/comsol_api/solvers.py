from __future__ import annotations

from typing import Any

from .utils import (
    apply_named_selections,
    apply_selection,
    label_if_present,
    set_indexed_properties,
    set_properties,
    set_property_groups,
)


def _build_solver_feature(parent, feature: dict[str, Any]) -> None:
    tag = str(feature["tag"])
    parent.create(tag, str(feature["api_type"]))
    feature_obj = parent.feature(tag)
    label_if_present(feature_obj, feature)
    apply_selection(feature_obj, feature.get("selection"))
    set_properties(feature_obj, feature.get("properties"))
    set_indexed_properties(feature_obj, feature.get("indexed_properties"))
    set_property_groups(feature_obj, feature.get("property_groups"))
    apply_named_selections(feature_obj, feature.get("named_selections"))
    for child in feature.get("features", []) or []:
        _build_solver_feature(feature_obj, child)


def build_solvers(java, plan: dict[str, Any]) -> None:
    for solver in plan.get("solvers", []) or []:
        tag = str(solver["tag"])
        java.sol().create(tag)
        sol = java.sol(tag)
        label_if_present(sol, solver)
        if "study" in solver:
            sol.study(str(solver["study"]))
        for feature in solver.get("features", []) or []:
            _build_solver_feature(sol, feature)


def run_solvers(java, plan: dict[str, Any]) -> None:
    for solver in plan.get("solvers", []) or []:
        if solver.get("run", False):
            java.sol(str(solver["tag"])).runAll()
