from __future__ import annotations

import argparse
import json
import sys
import time
from contextlib import suppress
from pathlib import Path
from typing import Any

import mph
import numpy as np
import yaml

from common import configure_mph, ensure_project_dirs, load_config, workspace
from comsol_api.executor import OfficialPlanExecutor


def load_plan(path: str | Path) -> dict[str, Any]:
    file = Path(path)
    if not file.exists():
        raise FileNotFoundError(file)
    plan = yaml.safe_load(file.read_text(encoding="utf-8"))
    if not isinstance(plan, dict):
        raise ValueError(f"Plan must be a YAML mapping: {file}")
    return plan


def resolve_workspace_path(root: Path, value: str | None, fallback: str) -> Path:
    raw = value or fallback
    path = Path(raw)
    if path.is_absolute():
        return path
    return root / path


def evaluate_outputs(model, outputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for output in outputs:
        expression = str(output.get("expression", "")).strip()
        if not expression:
            continue
        output_type = str(output.get("type", "stats"))
        values = np.asarray(model.evaluate(expression), dtype=float)
        finite = values[np.isfinite(values)]
        if finite.size == 0:
            raise RuntimeError(f'Expression "{expression}" evaluated to no finite values.')
        item = {
            "name": output.get("name", expression),
            "type": output_type,
            "expression": expression,
            "shape": list(values.shape),
            "finite_count": int(finite.size),
        }
        if output_type == "raw":
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
    }

    try:
        client = mph.start(cores=int(config.get("cores", 1)))
        model = client.create(simulation_id)
        runner = OfficialPlanExecutor(model, plan)

        runner.apply_parameters()
        runner.build_components()
        runner.build_studies()

        if setup_file != solved_file:
            runner.save(setup_file)
            report["setup_size_bytes"] = setup_file.stat().st_size

        runner.run_studies()
        runner.build_results()
        report["outputs"] = evaluate_outputs(model, plan.get("outputs", []))

        runner.save(solved_file)
        report["solved_size_bytes"] = solved_file.stat().st_size
        report["elapsed_seconds"] = round(time.perf_counter() - started, 2)
        report["status"] = "ok"
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        if client is not None and model is not None:
            with suppress(Exception):
                client.remove(model)
        if client is not None:
            with suppress(Exception):
                client.disconnect()


if __name__ == "__main__":
    main()
