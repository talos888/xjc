from __future__ import annotations

import argparse
import json
import sys
import time
from contextlib import suppress
from pathlib import Path
from typing import Any

import mph

from common import configure_mph, ensure_project_dirs, load_config, workspace
from comsol_api.manifest import collect_existing_mesh_report, collect_model_manifest, file_sha256
from comsol_api.verification import collect_solution_report
from existing_model_common import (
    load_json_mapping,
    load_mapping,
    prepare_output_files,
    require_nonempty_string,
    resolve_path,
)
from run_from_plan import evaluate_outputs


def validate_modify_plan(plan: dict[str, Any]) -> None:
    if plan.get("operation") != "modify":
        raise ValueError('Modify plan requires operation: "modify"')
    if plan.get("capability_level") != "safe_v0":
        raise ValueError('First-generation modify requires capability_level: "safe_v0"')
    require_nonempty_string(plan, "job_id")
    source = plan.get("source_model")
    if not isinstance(source, dict):
        raise ValueError('"source_model" must be a mapping with file and expected_file_sha256.')
    require_nonempty_string(source, "file")
    require_nonempty_string(source, "expected_file_sha256")
    manifest = plan.get("manifest")
    if not isinstance(manifest, dict):
        raise ValueError('"manifest" must be a mapping with file.')
    require_nonempty_string(manifest, "file")
    ops = plan.get("ops")
    if not isinstance(ops, list) or not ops:
        raise ValueError('"ops" must contain at least one set_parameter operation.')
    for index, op in enumerate(ops):
        if not isinstance(op, dict) or op.get("op") != "set_parameter":
            raise ValueError(f"ops[{index}] is not a supported set_parameter operation.")
        for key in ("name", "expected_old_value", "value"):
            require_nonempty_string(op, key)
    actions = plan.get("actions")
    if not isinstance(actions, dict) or actions.get("clear_solution") is not True:
        raise ValueError("Safe V0 requires actions.clear_solution: true")
    studies = actions.get("solve_studies")
    if not isinstance(studies, list) or not studies:
        raise ValueError("Safe V0 requires a non-empty actions.solve_studies list.")


def _preflight_source_and_manifest(
    root: Path, plan: dict[str, Any]
) -> tuple[Path, dict[str, Any], str]:
    source_spec = plan["source_model"]
    source = resolve_path(root, require_nonempty_string(source_spec, "file"))
    if not source.is_file():
        raise FileNotFoundError(source)
    expected_sha = require_nonempty_string(source_spec, "expected_file_sha256")
    actual_sha = file_sha256(source)
    if actual_sha != expected_sha:
        raise ValueError(f"Source SHA mismatch: expected {expected_sha}, got {actual_sha}")
    manifest_file = resolve_path(root, require_nonempty_string(plan["manifest"], "file"))
    manifest = load_json_mapping(manifest_file)
    if manifest.get("source_file_sha256") != actual_sha:
        raise ValueError("Manifest source_file_sha256 does not match the current source model.")
    manifest_source = Path(str(manifest.get("source_model", ""))).resolve()
    if manifest_source != source:
        raise ValueError(f"Manifest source_model does not match source model: {manifest_source}")
    for op in plan["ops"]:
        name = require_nonempty_string(op, "name")
        if name not in manifest.get("parameters", {}):
            raise ValueError(f'Parameter "{name}" is absent from the inspected manifest.')
        expected_old = require_nonempty_string(op, "expected_old_value")
        if str(manifest["parameters"][name]) != expected_old:
            raise ValueError(
                f'Parameter "{name}" manifest value mismatch: expected {expected_old}, '
                f'got {manifest["parameters"][name]}'
            )
    return source, manifest, actual_sha


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    parser.add_argument("--config", default="runner_config.json")
    args = parser.parse_args()

    started = time.perf_counter()
    config = load_config(args.config)
    plan = load_mapping(args.plan)
    validate_modify_plan(plan)
    ensure_project_dirs(config)
    root = workspace(config)
    job_id = require_nonempty_string(plan, "job_id")
    source, inspected_manifest, source_sha_before = _preflight_source_and_manifest(root, plan)
    files = prepare_output_files(
        root, plan.get("save_policy", {}), job_id, default_model_name=f"{job_id}_solved.mph"
    )
    target = files["model"]
    if source == target:
        raise ValueError("Safe V0 requires source and target model files to differ.")
    report: dict[str, Any] = {
        "job_id": job_id,
        "operation": "modify",
        "capability_level": "safe_v0",
        "source_model": str(source),
        "source_file_sha256": source_sha_before,
        "target_model": str(target),
        "plan": str(Path(args.plan).resolve()),
        "python_executable": sys.executable,
        "changes": [],
    }

    configure_mph(mph, config)
    client = None
    model = None
    try:
        client = mph.start(cores=int(config.get("cores", 1)))
        model = client.load(source)
        java = model.java
        live_parameters = {
            str(name): str(java.param().get(str(name))) for name in list(java.param().varnames())
        }
        for op in plan["ops"]:
            name = require_nonempty_string(op, "name")
            expected_old = require_nonempty_string(op, "expected_old_value")
            if live_parameters.get(name) != expected_old:
                raise ValueError(
                    f'Parameter "{name}" live value mismatch: expected {expected_old}, '
                    f"got {live_parameters.get(name)}"
                )

        study_tags = [str(tag) for tag in list(java.study().tags())]
        solve_studies = [str(tag) for tag in plan["actions"]["solve_studies"]]
        missing_studies = [tag for tag in solve_studies if tag not in study_tags]
        if missing_studies:
            raise ValueError(f"Unknown solve study tags: {missing_studies}")

        for op in plan["ops"]:
            name = require_nonempty_string(op, "name")
            value = require_nonempty_string(op, "value")
            java.param().set(name, value)
            applied = str(java.param().get(name))
            if applied != value:
                raise RuntimeError(
                    f'Parameter "{name}" did not retain the requested expression: '
                    f"expected {value}, got {applied}"
                )
            report["changes"].append(
                {"op": "set_parameter", "name": name, "old_value": live_parameters[name], "value": value}
            )

        cleared_solutions = []
        for solution_tag in [str(tag) for tag in list(java.sol().tags())]:
            java.sol(solution_tag).clearSolutionData()
            cleared_solutions.append(solution_tag)
        report["cleared_solutions"] = cleared_solutions

        for study_tag in solve_studies:
            java.study(study_tag).run()
        report["solved_studies"] = solve_studies

        mesh_report, mesh_failures = collect_existing_mesh_report(java)
        report["meshes"] = mesh_report
        if mesh_failures:
            raise RuntimeError(f"Mesh verification failed: {mesh_failures}")
        verification_plan = {
            "studies": [{"tag": tag, "run": True} for tag in solve_studies],
            "verification": {"require_nonzero_dof": True},
        }
        solution_report, solution_failures = collect_solution_report(java, verification_plan)
        report["solutions"] = solution_report
        if solution_failures:
            raise RuntimeError(f"Solution verification failed: {solution_failures}")
        report["outputs"] = evaluate_outputs(model, plan.get("outputs", []), root)

        target.parent.mkdir(parents=True, exist_ok=True)
        model.save(target)
        if file_sha256(source) != source_sha_before:
            raise RuntimeError("Source model changed during modify operation.")
        new_manifest = collect_model_manifest(java, target)
        files["manifest"].write_text(json.dumps(new_manifest, indent=2), encoding="utf-8")
        report["target_file_sha256"] = new_manifest["source_file_sha256"]
        report["target_size_bytes"] = target.stat().st_size
        report["elapsed_seconds"] = round(time.perf_counter() - started, 2)
        report["status"] = "ok"
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        files["report"].write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        if client is not None and model is not None:
            with suppress(Exception):
                client.remove(model)
        if client is not None and not getattr(client, "standalone", False):
            with suppress(Exception):
                client.disconnect()


if __name__ == "__main__":
    main()
