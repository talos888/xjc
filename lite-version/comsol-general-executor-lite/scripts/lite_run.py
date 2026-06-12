from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from common import load_config, workspace
from compact_task import compile_task, load_task, normalize_output_dir


def write_status(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=True, separators=(",", ":")))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--config", default="runner_config.json")
    parser.add_argument("--timeout-seconds", type=float, required=True)
    parser.add_argument("--manifest")
    args = parser.parse_args()

    try:
        task_path = Path(args.task).resolve()
        config_path = Path(args.config).resolve()
        task = load_task(task_path)
        simulation_id = str(task.get("id", "lite-run"))
        config = load_config(config_path)
        root = workspace(config)
        output_dir = normalize_output_dir(task.get("output_dir"), simulation_id)
        artifact_dir = (root / output_dir).resolve()
        artifact_dir.relative_to(root)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = (
            Path(args.manifest).resolve()
            if args.manifest
            else artifact_dir / f"{simulation_id}_manifest.json"
        )
        console_path = artifact_dir / f"{simulation_id}_console.log"
        supervisor_path = artifact_dir / f"{simulation_id}_supervisor.json"
        manifest = compile_task(task)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    except Exception as exc:
        write_status(
            {
                "status": "failed",
                "gate": "setup_or_compile",
                "error": f"{type(exc).__name__}: {exc}",
            }
        )
        return 2

    scripts = Path(__file__).resolve().parent
    lint = subprocess.run(
        [sys.executable, str(scripts / "lint_plan.py"), "--plan", str(manifest_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    console_path.write_text(
        "[lint stdout]\n"
        + lint.stdout
        + "\n[lint stderr]\n"
        + lint.stderr,
        encoding="utf-8",
    )
    if lint.returncode != 0:
        write_status(
            {
                "status": "failed",
                "gate": "lint",
                "manifest": str(manifest_path),
                "log": str(console_path),
            }
        )
        return lint.returncode

    supervised = subprocess.run(
        [
            sys.executable,
            str(scripts / "run_supervised.py"),
            "--plan",
            str(manifest_path),
            "--config",
            str(config_path),
            "--timeout-seconds",
            str(args.timeout_seconds),
            "--report",
            str(supervisor_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    with console_path.open("a", encoding="utf-8") as handle:
        handle.write("\n[run stdout]\n")
        handle.write(supervised.stdout)
        handle.write("\n[run stderr]\n")
        handle.write(supervised.stderr)

    supervisor = {}
    if supervisor_path.is_file():
        supervisor = json.loads(supervisor_path.read_text(encoding="utf-8"))
    status = "passed" if supervised.returncode == 0 else "failed"
    payload = {
        "status": status,
        "gate": "complete" if status == "passed" else "execute",
        "manifest": str(manifest_path),
        "report": str(
            root
            / manifest.get("save_policy", {}).get(
                "report_file", f"project/lite/{simulation_id}/{simulation_id}_report.json"
            )
        ),
        "model": str(
            root
            / manifest.get("save_policy", {}).get(
                "solved_file", f"project/lite/{simulation_id}/{simulation_id}_solved.mph"
            )
        ),
        "supervisor": str(supervisor_path),
        "log": str(console_path),
        "elapsed_seconds": supervisor.get("elapsed_seconds"),
    }
    write_status(payload)
    return supervised.returncode


if __name__ == "__main__":
    raise SystemExit(main())
