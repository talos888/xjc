from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from comsol_api.registry import (
    GEOMETRY_FEATURES,
    PHYSICS_FEATURES,
    PHYSICS_INTERFACES,
    STUDY_TYPES,
)
from comsol_api.profiles import PROFILES
from comsol_api.preprocess import expand_manifest


UNIT_IN_FLOW_RE = re.compile(r"\[[^\]\n]*[A-Za-z_][^\]\n]*\[[^\]\n]+\][^\]\n]*\]")
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
MESH_GENERATOR_TYPES = {
    "FreeTri",
    "Map",
    "Mapped",
    "FreeTet",
    "Swept",
    "FreeQuad",
    "Edge",
}


def load_plan_text(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        value = json.loads(text)
    else:
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError("YAML plans require PyYAML; use JSON for the zero-dependency path.") from exc
        value = yaml.safe_load(text)
    if not isinstance(value, dict):
        raise ValueError("Plan must be a mapping.")
    return expand_manifest(value)


def duplicate_values(values: list[str]) -> set[str]:
    return {value for value in values if values.count(value) > 1}


def has_registered_or_explicit(spec: dict[str, Any], registry: dict, label: str) -> list[str]:
    if spec.get("api_type") or spec.get("existing"):
        return []
    official_name = str(spec.get("official_name", "")).strip()
    if official_name in registry:
        return []
    return [f"{label} {spec.get('tag', '<untagged>')} lacks registered official_name/api_type"]


def validate_profile(spec: dict[str, Any], label: str) -> list[str]:
    name = spec.get("profile")
    if name and name not in PROFILES:
        return [f"{label} {spec.get('tag', '<untagged>')} uses unknown profile {name}"]
    return []


def validate_indexed_properties(spec: dict[str, Any], label: str) -> list[str]:
    issues: list[str] = []
    indexed = spec.get("indexed_properties", []) or []
    if not isinstance(indexed, list):
        return [f"{label} {spec.get('tag', '<untagged>')} indexed_properties must be a list"]
    for number, item in enumerate(indexed, start=1):
        if not isinstance(item, dict):
            issues.append(
                f"{label} {spec.get('tag', '<untagged>')} "
                f"indexed_properties[{number}] must be a mapping"
            )
            continue
        for key in ("property", "index", "value"):
            if key not in item:
                issues.append(
                    f"{label} {spec.get('tag', '<untagged>')} indexed_properties[{number}] lacks {key}"
                )
        for key in ("index", "outer_index"):
            if key in item:
                try:
                    int(item[key])
                except (TypeError, ValueError):
                    issues.append(
                        f"{label} {spec.get('tag', '<untagged>')} "
                        f"indexed_properties[{number}] {key} must be int"
                    )
    return issues


def validate_property_groups(spec: dict[str, Any], label: str) -> list[str]:
    issues: list[str] = []
    groups = spec.get("property_groups", []) or []
    if not isinstance(groups, list):
        return [f"{label} {spec.get('tag', '<untagged>')} property_groups must be a list"]
    for number, group in enumerate(groups, start=1):
        if not isinstance(group, dict):
            issues.append(
                f"{label} {spec.get('tag', '<untagged>')} property_groups[{number}] must be a mapping"
            )
            continue
        if "group" not in group and "tag" not in group:
            issues.append(
                f"{label} {spec.get('tag', '<untagged>')} property_groups[{number}] lacks group/tag"
            )
        issues.extend(validate_indexed_properties(group, f"{label} property group"))
    return issues


def validate_feature_tree(items: list[dict[str, Any]], label: str) -> list[str]:
    issues: list[str] = []
    for item in items or []:
        if "tag" not in item or "api_type" not in item:
            issues.append(f"{label} feature lacks tag/api_type")
        issues.extend(validate_indexed_properties(item, label))
        children = item.get("features", []) or []
        if children:
            issues.extend(validate_feature_tree(children, label))
    return issues


def lint_plan(plan: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if "simulation_id" not in plan:
        issues.append("Missing top-level simulation_id")
    elif not SAFE_ID_RE.match(str(plan["simulation_id"])):
        issues.append("simulation_id must be file-safe ASCII: letters, numbers, dot, dash, underscore")
    save_policy = plan.get("save_policy", {}) or {}
    if not isinstance(save_policy, dict):
        issues.append("save_policy must be a mapping")
    elif not save_policy.get("solved_file") and not save_policy.get("output_dir"):
        issues.append("save_policy should include solved_file or output_dir")
    if "components" not in plan:
        issues.append("Missing top-level components")
    if "studies" not in plan:
        issues.append("Missing top-level studies")

    component_tag_list = [
        str(component.get("tag", "comp1")) for component in plan.get("components", []) or []
    ]
    component_tags = set(component_tag_list)
    physics_tags_by_component = {
        str(component.get("tag", "comp1")): {
            str(physics["tag"])
            for physics in component.get("physics", []) or []
            if "tag" in physics
        }
        for component in plan.get("components", []) or []
    }
    study_tags = {
        str(study.get("tag", "std1")) for study in plan.get("studies", []) or []
    }
    table_tags = {
        str(table["tag"]) for table in plan.get("tables", []) or [] if "tag" in table
    }
    for label, tags in (
        ("component", component_tag_list),
        ("study", [str(item.get("tag", "std1")) for item in plan.get("studies", []) or []]),
        ("table", [str(item["tag"]) for item in plan.get("tables", []) or [] if "tag" in item]),
        ("solver", [str(item["tag"]) for item in plan.get("solvers", []) or [] if "tag" in item]),
    ):
        for tag in sorted(duplicate_values(tags)):
            issues.append(f"Duplicate {label} tag: {tag}")

    for component in plan.get("components", []) or []:
        for label, items in (
            ("geometry feature", component.get("geometry", {}).get("features", []) or []),
            ("selection", component.get("selections", []) or []),
            ("material", component.get("materials", []) or []),
            ("physics", component.get("physics", []) or []),
            ("mesh feature", component.get("mesh", {}).get("features", []) or []),
        ):
            tags = [str(item["tag"]) for item in items if "tag" in item]
            for tag in sorted(duplicate_values(tags)):
                issues.append(
                    f"Component {component.get('tag', '<untagged>')} has duplicate {label} tag: {tag}"
                )
        geometry_features = component.get("geometry", {}).get("features", []) or []
        if not geometry_features:
            issues.append(f"Component {component.get('tag', '<untagged>')} geometry has no features")
        for feature in geometry_features:
            issues.extend(has_registered_or_explicit(feature, GEOMETRY_FEATURES, "Geometry"))
            issues.extend(validate_indexed_properties(feature, "Geometry"))
        for selection in component.get("selections", []) or []:
            if not selection.get("api_type"):
                issues.append(f"Selection {selection.get('tag', '<untagged>')} lacks api_type")
            issues.extend(validate_indexed_properties(selection, "Selection"))
        for material in component.get("materials", []) or []:
            issues.extend(validate_indexed_properties(material, "Material"))
            issues.extend(validate_property_groups(material, "Material"))
            for group in material.get("property_groups", []) or []:
                issues.extend(validate_indexed_properties(group, "Material property group"))
        for physics in component.get("physics", []) or []:
            issues.extend(validate_profile(physics, "Physics"))
            issues.extend(has_registered_or_explicit(physics, PHYSICS_INTERFACES, "Physics"))
            issues.extend(validate_indexed_properties(physics, "Physics"))
            issues.extend(validate_property_groups(physics, "Physics"))
            for feature in physics.get("features", []) or []:
                issues.extend(validate_profile(feature, "Physics feature"))
                issues.extend(has_registered_or_explicit(feature, PHYSICS_FEATURES, "Physics feature"))
                issues.extend(validate_indexed_properties(feature, "Physics feature"))
                issues.extend(validate_property_groups(feature, "Physics feature"))
        mesh = component.get("mesh", {}) or {}
        mesh_features = mesh.get("features", []) or []
        if "auto_size" not in mesh and not mesh_features:
            issues.append(f"Component {component.get('tag', '<untagged>')} mesh has no auto_size/features")
        api_types = {str(feature.get("api_type", "")) for feature in mesh_features}
        if api_types and not (api_types & MESH_GENERATOR_TYPES):
            issues.append(
                f"Component {component.get('tag', '<untagged>')} mesh features lack a mesh generator"
            )
        issues.extend(validate_feature_tree(mesh_features, "Mesh"))

    for study in plan.get("studies", []) or []:
        for feature in study.get("features", []) or []:
            issues.extend(has_registered_or_explicit(feature, STUDY_TYPES, "Study feature"))
            issues.extend(validate_indexed_properties(feature, "Study feature"))

    for field in ("variables", "couplings", "tables", "derived_values", "numerical_results", "plots", "exports", "solvers"):
        for item in plan.get(field, []) or []:
            if "tag" not in item:
                issues.append(f"{field} item lacks tag")
            issues.extend(validate_indexed_properties(item, field))
            if field == "solvers":
                issues.extend(
                    validate_feature_tree(
                        item.get("features", []) or [],
                        f"Solver {item.get('tag', '<untagged>')}",
                    )
                )

    for field in ("couplings", "derived_values", "plots", "exports"):
        for item in plan.get(field, []) or []:
            if "api_type" not in item:
                issues.append(f"{field} item {item.get('tag', '<untagged>')} lacks api_type")

    for coupling in plan.get("couplings", []) or []:
        if str(coupling.get("component", "")) not in component_tags:
            issues.append(
                f"coupling {coupling.get('tag', '<untagged>')} references unknown component"
            )

    for value in plan.get("derived_values", []) or []:
        if "table" in value and str(value["table"]) not in table_tags:
            issues.append(
                f"derived_values item {value.get('tag', '<untagged>')} references unknown table"
            )

    for solver in plan.get("solvers", []) or []:
        if "study" in solver and str(solver["study"]) not in study_tags:
            issues.append(f"solver {solver.get('tag', '<untagged>')} references unknown study")

    for plot in plan.get("plots", []) or plan.get("results", []) or []:
        for feature in plot.get("features", []) or []:
            if "tag" not in feature or "api_type" not in feature:
                issues.append(f"plot feature in {plot.get('tag', '<untagged>')} lacks tag/api_type")
            issues.extend(validate_indexed_properties(feature, "Plot feature"))

    for output in plan.get("outputs", []) or []:
        if not str(output.get("expression", "")).strip():
            issues.append(f"output {output.get('name', '<unnamed>')} lacks expression")
        if "complex_mode" in output and output["complex_mode"] not in {
            "magnitude",
            "real",
            "imag",
            "phase",
        }:
            issues.append(
                f"output {output.get('name', '<unnamed>')} has invalid complex_mode"
            )
        if "reference_expression" in output:
            if not str(output.get("reference_expression", "")).strip():
                issues.append(
                    f"output {output.get('name', '<unnamed>')} has empty reference_expression"
                )
            metric = output.get("comparison_metric", "relative_l2")
            if metric not in {"max_abs", "rmse", "relative_l2"}:
                issues.append(
                    f"output {output.get('name', '<unnamed>')} has invalid comparison_metric"
                )

    for field in ("ports", "scattering_boundaries", "pml"):
        for item in plan.get(field, []) or []:
            for key in ("component", "tag"):
                if key not in item:
                    issues.append(f"{field} item lacks {key}")
            if field != "pml" and "physics" not in item:
                issues.append(f"{field} item {item.get('tag', '<untagged>')} lacks physics")
            component_tag = str(item.get("component", ""))
            if component_tag not in component_tags:
                issues.append(f"{field} item {item.get('tag', '<untagged>')} references unknown component")
            elif field != "pml" and str(item.get("physics", "")) not in physics_tags_by_component.get(
                component_tag, set()
            ):
                issues.append(f"{field} item {item.get('tag', '<untagged>')} references unknown physics")
            issues.extend(validate_indexed_properties(item, field))

    return issues


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    args = parser.parse_args()

    path = Path(args.plan)
    text = path.read_text(encoding="utf-8")
    hints = []
    if UNIT_IN_FLOW_RE.search(text):
        hints.append(
            "Possible unquoted COMSOL unit expression inside a flow list. "
            "Use quotes, e.g. ['1[V/m]', '0', '0']."
        )
    try:
        plan = load_plan_text(path)
    except Exception as exc:
        print(json.dumps({"ok": False, "parse_error": str(exc), "hints": hints}, indent=2))
        raise SystemExit(1)

    issues = lint_plan(plan)
    ok = not issues
    print(json.dumps({"ok": ok, "issues": issues, "hints": hints}, indent=2))
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
