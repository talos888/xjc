from __future__ import annotations

from typing import Any
import struct


def _as_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    try:
        return list(value)
    except TypeError:
        return [value]


def _solution_size_values(value: Any) -> list[int | None]:
    if isinstance(value, (bytes, bytearray)):
        if len(value) % 4:
            return []
        return [int(item) for item in struct.unpack("<" + "i" * (len(value) // 4), value)]
    return [_as_int(item) for item in _as_list(value)]


def collect_mesh_report(java, plan: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    report: dict[str, Any] = {}
    failures: list[str] = []
    for component in plan.get("components", []) or []:
        component_tag = str(component.get("tag", "comp1"))
        mesh = component.get("mesh", {}) or {}
        mesh_tag = str(mesh.get("tag", "mesh1"))
        key = f"{component_tag}/{mesh_tag}"
        item: dict[str, Any] = {"require_nonzero_elements": bool(mesh.get("require_nonzero_elements", True))}
        try:
            count = _as_int(java.component(component_tag).mesh(mesh_tag).getNumElem())
            item["num_elements"] = count
            if item["require_nonzero_elements"] and (count is None or count <= 0):
                failures.append(f"Mesh {key} has zero elements.")
        except Exception as exc:
            item["error"] = f"{type(exc).__name__}: {exc}"
            if item["require_nonzero_elements"]:
                failures.append(f"Mesh {key} element count could not be verified.")
        report[key] = item
    return report, failures


def collect_solution_report(java, plan: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    report: dict[str, Any] = {}
    failures: list[str] = []
    verification = plan.get("verification", {}) or {}
    require_nonzero_dof = bool(verification.get("require_nonzero_dof", True))
    solver_tags = [str(item["tag"]) for item in plan.get("solvers", []) or [] if "tag" in item]
    if not solver_tags:
        try:
            solver_tags = [str(tag) for tag in _as_list(java.sol().tags())]
        except Exception:
            solver_tags = []
    expects_solution = any(study.get("run", True) for study in plan.get("studies", []) or []) or any(
        solver.get("run", False) for solver in plan.get("solvers", []) or []
    )
    if require_nonzero_dof and expects_solution and not solver_tags:
        failures.append("No solution sequence was found after running the plan.")

    solver_specs = {
        str(item["tag"]): item for item in plan.get("solvers", []) or [] if "tag" in item
    }
    per_solver = verification.get("solvers", {}) or {}
    for tag in solver_tags:
        item: dict[str, Any] = {"require_nonzero_dof": require_nonzero_dof}
        try:
            size = _solution_size_values(java.sol(tag).getSize())
            item["size"] = size
            dof = next((value for value in size if value is not None), None)
            if require_nonzero_dof and (dof is None or dof <= 0):
                failures.append(f"Solution {tag} has zero DOF.")
        except Exception as exc:
            item["error"] = f"{type(exc).__name__}: {exc}"
        try:
            item["parameter_values"] = [float(value) for value in _as_list(java.sol(tag).getPVals())]
            expected = (
                (per_solver.get(tag, {}) or {}).get("expected_stored_points")
                or (solver_specs.get(tag, {}).get("verification", {}) or {}).get(
                    "expected_stored_points"
                )
                or verification.get("expected_stored_points")
            )
            if expected is not None and len(item["parameter_values"]) != int(expected):
                failures.append(
                    f"Solution {tag} stores {len(item['parameter_values'])} points; "
                    f"expected {int(expected)}."
                )
        except Exception:
            pass
        report[tag] = item
    return report, failures


def collect_results_report(java, plan: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    report: dict[str, Any] = {}
    failures: list[str] = []
    expected = plan.get("verification", {}).get("required_result_tags", []) or []
    try:
        tags = [str(tag) for tag in _as_list(java.result().tags())]
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}, ["Results tree could not be read."]
    report["plot_group_tags"] = tags
    for tag in expected:
        if str(tag) not in tags:
            failures.append(f"Required result tag {tag} is missing.")
    try:
        report["table_tags"] = [str(tag) for tag in _as_list(java.result().table().tags())]
    except Exception:
        report["table_tags"] = []
    try:
        report["numerical_tags"] = [str(tag) for tag in _as_list(java.result().numerical().tags())]
    except Exception:
        report["numerical_tags"] = []
    for tag in plan.get("verification", {}).get("required_table_tags", []) or []:
        if str(tag) not in report["table_tags"]:
            failures.append(f"Required result table {tag} is missing.")
    for tag in plan.get("verification", {}).get("required_numerical_tags", []) or []:
        if str(tag) not in report["numerical_tags"]:
            failures.append(f"Required numerical result {tag} is missing.")
    return report, failures
