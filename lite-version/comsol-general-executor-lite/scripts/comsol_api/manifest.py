from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    try:
        return list(value)
    except TypeError:
        return [value]


def _tags(node) -> list[str]:
    return [str(value) for value in _as_list(node.tags())]


def collect_existing_mesh_report(java) -> tuple[dict[str, Any], list[str]]:
    meshes: dict[str, Any] = {}
    failures: list[str] = []
    for component_tag in _tags(java.component()):
        meshes[component_tag] = {}
        for mesh_tag in _tags(java.component(component_tag).mesh()):
            item: dict[str, Any] = {}
            key = f"{component_tag}/{mesh_tag}"
            try:
                count = int(java.component(component_tag).mesh(mesh_tag).getNumElem())
                item["num_elements"] = count
                if count <= 0:
                    failures.append(f"Mesh {key} has zero elements.")
            except Exception as exc:
                item["error"] = f"{type(exc).__name__}: {exc}"
                failures.append(f"Mesh {key} element count could not be verified.")
            meshes[component_tag][mesh_tag] = item
    if not meshes:
        failures.append("No component meshes were found.")
    return meshes, failures


def collect_model_manifest(java, model_file: str | Path) -> dict[str, Any]:
    path = Path(model_file).resolve()
    components = _tags(java.component())
    studies = _tags(java.study())
    solutions = _tags(java.sol())
    datasets = _tags(java.result().dataset())

    parameters = {
        str(name): str(java.param().get(str(name))) for name in _as_list(java.param().varnames())
    }
    meshes, mesh_failures = collect_existing_mesh_report(java)
    component_tree: dict[str, Any] = {}
    for component_tag in components:
        component = java.component(component_tag)
        item: dict[str, Any] = {}
        try:
            material_tags = _tags(component.material())
        except Exception:
            material_tags = []
        item["materials"] = material_tags
        physics_tree: dict[str, Any] = {}
        try:
            physics_tags = _tags(component.physics())
        except Exception:
            physics_tags = []
        for physics_tag in physics_tags:
            physics_item: dict[str, Any] = {}
            try:
                physics_item["features"] = _tags(component.physics(physics_tag).feature())
            except Exception:
                physics_item["features"] = []
            physics_tree[physics_tag] = physics_item
        item["physics"] = physics_tree
        try:
            item["selections"] = _tags(component.selection())
        except Exception:
            item["selections"] = []
        component_tree[component_tag] = item

    results_tree: dict[str, Any] = {}
    for name, getter in (
        ("plot_groups", lambda: java.result()),
        ("tables", lambda: java.result().table()),
        ("numerical", lambda: java.result().numerical()),
        ("exports", lambda: java.result().export()),
    ):
        try:
            results_tree[name] = _tags(getter())
        except Exception:
            results_tree[name] = []

    solution_state: dict[str, Any] = {}
    for solution_tag in solutions:
        item: dict[str, Any] = {}
        try:
            item["size"] = [int(value) for value in _as_list(java.sol(solution_tag).getSize())]
        except Exception as exc:
            item["size_error"] = f"{type(exc).__name__}: {exc}"
        try:
            item["parameter_values"] = [
                float(value) for value in _as_list(java.sol(solution_tag).getPVals())
            ]
        except Exception:
            pass
        solution_state[solution_tag] = item

    return {
        "manifest_version": "inspect-safe-v0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_model": str(path),
        "source_file_sha256": file_sha256(path),
        "source_size_bytes": path.stat().st_size,
        "parameters": parameters,
        "tags": {
            "components": components,
            "studies": studies,
            "solutions": solutions,
            "datasets": datasets,
        },
        "meshes": meshes,
        "mesh_failures": mesh_failures,
        "component_tree": component_tree,
        "results_tree": results_tree,
        "solution_state": solution_state,
    }
