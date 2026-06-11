from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def terminate_process_tree(process: subprocess.Popen[str]) -> dict[str, object]:
    """Terminate only the process tree created by this supervisor."""
    if process.poll() is not None:
        return {"attempted": False, "reason": "already_exited"}
    if os.name == "nt":
        completed = subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            text=True,
            check=False,
        )
        return {
            "attempted": True,
            "tool": "taskkill",
            "returncode": completed.returncode,
            "stdout": completed.stdout[-2000:],
            "stderr": completed.stderr[-2000:],
        }
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=10)
        return {"attempted": True, "tool": "SIGTERM", "returncode": process.returncode}
    except (ProcessLookupError, subprocess.TimeoutExpired):
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
        return {"attempted": True, "tool": "SIGKILL", "returncode": process.poll()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    parser.add_argument("--config", default="runner_config.json")
    parser.add_argument("--timeout-seconds", type=float, required=True)
    parser.add_argument("--report")
    args = parser.parse_args()
    if args.timeout_seconds <= 0:
        raise ValueError("--timeout-seconds must be positive")

    plan_path = Path(args.plan).resolve()
    config_path = Path(args.config).resolve()
    if not plan_path.is_file():
        raise FileNotFoundError(plan_path)
    if not config_path.is_file():
        raise FileNotFoundError(config_path)
    script = Path(__file__).with_name("run_from_plan.py")
    command = [
        sys.executable,
        str(script),
        "--plan",
        str(plan_path),
        "--config",
        str(config_path),
    ]
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    started = time.perf_counter()
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=creationflags,
        start_new_session=os.name != "nt",
    )
    timed_out = False
    termination: dict[str, object] | None = None
    try:
        stdout, stderr = process.communicate(timeout=args.timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        termination = terminate_process_tree(process)
        try:
            stdout, stderr = process.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate(timeout=10)

    report = {
        "status": "timeout"
        if timed_out
        else ("ok" if process.returncode == 0 else "failed"),
        "timed_out": timed_out,
        "timeout_seconds": args.timeout_seconds,
        "elapsed_seconds": round(time.perf_counter() - started, 2),
        "returncode": process.returncode,
        "command": command,
        "stdout_tail": stdout[-8000:],
        "stderr_tail": stderr[-8000:],
        "child_pid": process.pid,
        "termination": termination,
    }
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report["supervisor_report"] = str(report_path.resolve())
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True))
    raise SystemExit(124 if timed_out else process.returncode)


if __name__ == "__main__":
    main()
