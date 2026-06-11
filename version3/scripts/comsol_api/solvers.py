from __future__ import annotations

from typing import Any

from .utils import label_if_present, set_indexed_properties, set_properties


def build_solvers(java, plan: dict[str, Any]) -> None:
    for solver in plan.get("solvers", []) or []:
        tag = str(solver["tag"])
        java.sol().create(tag)
        sol = java.sol(tag)
        label_if_present(sol, solver)
        if "study" in solver:
            sol.study(str(solver["study"]))
        for feature in solver.get("features", []) or []:
            ftag = str(feature["tag"])
            sol.create(ftag, str(feature["api_type"]))
            feature_obj = sol.feature(ftag)
            label_if_present(feature_obj, feature)
            set_properties(feature_obj, feature.get("properties"))
            set_indexed_properties(feature_obj, feature.get("indexed_properties"))


def run_solvers(java, plan: dict[str, Any]) -> None:
    for solver in plan.get("solvers", []) or []:
        if solver.get("run", False):
            java.sol(str(solver["tag"])).runAll()
