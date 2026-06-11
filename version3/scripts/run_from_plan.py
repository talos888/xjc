from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from contextlib import suppress
from pathlib import Path
from typing import Any

import mph
import numpy as np
from common import configure_mph, ensure_project_dirs, load_config, workspace
from comsol_api.executor import OfficialPlanExecutor
from comsol_api.verification import (
    collect_mesh_report,
    collect_results_report,
    collect_solution_report,
)
from lint_plan import lint_plan, load_plan_text


def load_plan(path: str | Path) -> dict[str, Any]:
    file = Path(path)
    if not file.exists():
        raise FileNotFoundError(file)
    return load_plan_text(file)


def resolve_workspace_path(root: Path, value: str | None, fallback: str) -> Path:
    raw = value or fallback
    path = Path(raw)
    if path.is_absolute():
        return path
    return root / path


def as_array(value: Any, complex_mode: str | None = None) -> np.ndarray:
    values = np.asarray(value)
    if values.shape == ():
        values = values.reshape(1)
    if np.iscomplexobj(values):
        if complex_mode == "magnitude":
            values = np.abs(values)
        elif complex_mode == "real":
            values = np.real(values)
        elif complex_mode == "imag":
            values = np.imag(values)
        elif complex_mode == "phase":
            values = np.angle(values)
        else:
            raise ValueError(
                "Complex output requires complex_mode: magnitude, real, imag, or phase."
            )
    return np.asarray(values, dtype=float)


def evaluate_outputs(
    model, outputs: list[dict[str, Any]], root: Path
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for output in outputs:
        expression = str(output.get("expression", "")).strip()
        if not expression:
            continue
        output_type = str(output.get("type", "stats"))
        evaluate_args: dict[str, Any] = {}
        for key in ("unit", "dataset", "inner", "outer"):
            if key in output:
                evaluate_args[key] = output[key]
        complex_mode = output.get("complex_mode")
        values = as_array(model.evaluate(expression, **evaluate_args), complex_mode)
        finite = values[np.isfinite(values)]
        if finite.size == 0:
            raise RuntimeError(f'Expression "{expression}" evaluated to no finite values.')
        item = {
            "name": output.get("name", expression),
            "type": output_type,
            "expression": expression,
            "evaluation": evaluate_args,
            "complex_mode": complex_mode,
            "shape": list(values.shape),
            "finite_count": int(finite.size),
        }
        artifact = output.get("artifact")
        if artifact:
            artifact_path = resolve_workspace_path(root, str(artifact), str(artifact))
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            with artifact_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["index", "value"])
                for index, value in enumerate(values.reshape(-1)):
                    writer.writerow([index, float(value)])
            item["artifact"] = str(artifact_path.resolve())
        if output_type == "scalar":
            item["value"] = float(finite.reshape(-1)[0])
        elif output_type == "raw":
            limit = int(output.get("limit", 20))
            item["values"] = [float(value) for value in finite[:limit]]
            item["truncated"] = bool(finite.size > limit)
        else:
            item.update(
                {
                    "min": float(np.min(finite)),
                    "max": float(np.max(finite)),
                    "mean": float(np.mean(finite)),
                }
            )
        checks = output.get("checks", {})
        if checks:
            failures = []
            if checks.get("finite") and finite.size == 0:
                failures.append("finite_count=0")
            if "count_gte" in checks and finite.size < int(checks["count_gte"]):
                failures.append(f"finite_count={finite.size} < {checks['count_gte']}")
            if "count_lte" in checks and finite.size > int(checks["count_lte"]):
                failures.append(f"finite_count={finite.size} > {checks['count_lte']}")
            for key, actual in (
                ("min", item.get("min", item.get("value"))),
                ("max", item.get("max", item.get("value"))),
                ("mean", item.get("mean", item.get("value"))),
                ("value", item.get("value")),
            ):
                if actual is None:
                    continue
                if f"{key}_gt" in checks and not actual > float(checks[f"{key}_gt"]):
                    failures.append(f"{key}={actual} <= {checks[f'{key}_gt']}")
                if f"{key}_gte" in checks and actual < float(checks[f"{key}_gte"]):
                    failures.append(f"{key}={actual} < {checks[f'{key}_gte']}")
                if f"{key}_lt" in checks and not actual < float(checks[f"{key}_lt"]):
                    failures.append(f"{key}={actual} >= {checks[f'{key}_lt']}")
                if f"{key}_lte" in checks and actual > float(checks[f"{key}_lte"]):
                    failures.append(f"{key}={actual} > {checks[f'{key}_lte']}")
            item["check_failures"] = failures
            if failures:
                raise RuntimeError(f"Output checks failed for {expression}: {failures}")
        results.append(item)
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", default="run_plan.yaml")
    parser.add_argument("--config", default="runner_config.json")
    args = parser.parse_args()

    started = time.perf_counter()
    config = load_config(args.config)
    plan = load_plan(args.plan)
    lint_issues = lint_plan(plan)
    if lint_issues:
        raise ValueError(f"Plan lint failed: {lint_issues}")
    ensure_project_dirs(config)
    root = workspace(config)

    simulation_id = str(plan.get("simulation_id") or plan.get("simulation_name") or "comsol_run")
    save_policy = plan.get("save_policy", {})
    overwrite = bool(save_policy.get("overwrite", False))
    setup_file = resolve_workspace_path(
        root, save_policy.get("setup_file"), f"project/runs/{simulation_id}_setup.mph"
    )
    solved_file = resolve_workspace_path(
        root, save_policy.get("solved_file"), f"project/runs/{simulation_id}_solved.mph"
    )
    report_file = resolve_workspace_path(
        root, save_policy.get("report_file"), f"project/runs/{simulation_id}_run_report.json"
    )
    event_file = resolve_workspace_path(
        root, save_policy.get("event_file"), f"project/runs/{simulation_id}_events.jsonl"
    )

    for file in (setup_file, solved_file, report_file):
        if file.exists() and not overwrite:
            raise FileExistsError(f"Refusing to overwrite existing file: {file}")

    configure_mph(mph, config)
    client = None
    model = None
    report: dict[str, Any] = {
        "simulation_id": simulation_id,
        "python_executable": sys.executable,
        "plan": str(Path(args.plan).resolve()),
        "setup_file": str(setup_file.resolve()),
        "solved_file": str(solved_file.resolve()),
        "simulation_intent": plan.get("simulation_intent"),
        "assumptions": plan.get("assumptions", []),
        "unresolved_questions": plan.get("unresolved_questions", []),
        "manifest_bytes": Path(args.plan).stat().st_size,
        "expanded_manifest_bytes": len(
            json.dumps(plan, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
        ),
    }

    def event(stage: str, status: str, **details: Any) -> None:
        event_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "stage": stage,
            "status": status,
            **details,
        }
        with event_file.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True, default=str) + "\n")

    try:
        event("startup", "start")
        client = mph.start(cores=int(config.get("cores", 1)))
        model = client.create(simulation_id)
        runner = OfficialPlanExecutor(model, plan)

        runner.apply_parameters()
        runner.build_components()
        runner.build_variables()
        runner.build_couplings()
        runner.build_wave_optics_helpers()
        runner.build_studies()
        runner.build_solvers()
        event("build", "pass")

        if setup_file != solved_file:
            runner.save(setup_file)
            report["setup_size_bytes"] = setup_file.stat().st_size

        runner.run_solvers()
        runner.run_studies()
        mesh_report, mesh_failures = collect_mesh_report(model.java, plan)
        solution_report, solution_failures = collect_solution_report(model.java, plan)
        report["mesh"] = mesh_report
        report["solutions"] = solution_report
        verification_failures = mesh_failures + solution_failures
        if verification_failures:
            report["verification_failures"] = verification_failures
            raise RuntimeError(f"Verification failed: {verification_failures}")
        event("solve", "pass")
        runner.build_result_tables()
        runner.build_results()
        runner.build_derived_values()
        runner.build_numerical_results()
        runner.build_exports()
        results_report, results_failures = collect_results_report(model.java, plan)
        report["results"] = results_report
        if results_failures:
            raise RuntimeError(f"Results verification failed: {results_failures}")
        report["outputs"] = evaluate_outputs(model, plan.get("outputs", []), root)

        runner.save(solved_file)
        report["solved_size_bytes"] = solved_file.stat().st_size
        if plan.get("verification", {}).get("reload_results", True):
            client.remove(model)
            model = client.load(solved_file)
            reload_report, reload_failures = collect_results_report(model.java, plan)
            report["results_after_reload"] = reload_report
            if reload_failures:
                raise RuntimeError(f"Reload Results verification failed: {reload_failures}")
        report["elapsed_seconds"] = round(time.perf_counter() - started, 2)
        report["status"] = "ok"
        event("complete", "pass", report=str(report_file), solved_model=str(solved_file))
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = f"{type(exc).__name__}: {exc}"
        event("failed", "fail", error=report["error"])
        raise
    finally:
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
        compact = {
            "status": report.get("status"),
            "simulation_id": simulation_id,
            "report": str(report_file.resolve()),
            "setup_model": str(setup_file.resolve()),
            "solved_model": str(solved_file.resolve()),
            "error": report.get("error"),
        }
        print(json.dumps(compact, ensure_ascii=True))
        if client is not None and model is not None:
            with suppress(Exception):
                client.remove(model)
        if client is not None and not getattr(client, "standalone", False):
            with suppress(Exception):
                client.disconnect()


if __name__ == "__main__":
    main()
