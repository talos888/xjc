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
from comsol_api.manifest import collect_model_manifest
from existing_model_common import load_mapping, prepare_output_files, require_nonempty_string, resolve_path


def validate_inspect_plan(plan: dict[str, Any]) -> None:
    if plan.get("operation") != "inspect":
        raise ValueError('Inspect plan requires operation: "inspect"')
    require_nonempty_string(plan, "job_id")
    require_nonempty_string(plan, "source_model")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    parser.add_argument("--config", default="runner_config.json")
    args = parser.parse_args()

    started = time.perf_counter()
    config = load_config(args.config)
    plan = load_mapping(args.plan)
    validate_inspect_plan(plan)
    ensure_project_dirs(config)
    root = workspace(config)
    job_id = require_nonempty_string(plan, "job_id")
    source = resolve_path(root, require_nonempty_string(plan, "source_model"))
    if not source.is_file():
        raise FileNotFoundError(source)
    files = prepare_output_files(root, plan.get("save_policy", {}), job_id)
    report: dict[str, Any] = {
        "job_id": job_id,
        "operation": "inspect",
        "source_model": str(source),
        "plan": str(Path(args.plan).resolve()),
        "manifest_file": str(files["manifest"]),
        "python_executable": sys.executable,
    }

    configure_mph(mph, config)
    client = None
    model = None
    try:
        client = mph.start(cores=int(config.get("cores", 1)))
        model = client.load(source)
        manifest = collect_model_manifest(model.java, source)
        files["manifest"].write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        report["summary"] = {
            "parameter_count": len(manifest["parameters"]),
            "components": manifest["tags"]["components"],
            "studies": manifest["tags"]["studies"],
            "solutions": manifest["tags"]["solutions"],
            "datasets": manifest["tags"]["datasets"],
        }
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
