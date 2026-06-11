from __future__ import annotations

import ast
import json
import shutil
import uuid
from pathlib import Path

from audit import append_event, protect_target
from comsol_api import assert_count, validate_tensor3
from validate_case_evidence import validate


def expect_failure(label: str, callback) -> dict[str, str]:
    try:
        callback()
    except Exception as error:
        return {"label": label, "status": "pass", "error": f"{type(error).__name__}: {error}"}
    return {"label": label, "status": "fail", "error": "failure_not_detected"}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    checks: list[dict[str, str]] = []

    for script in sorted((root / "scripts").glob("*.py")):
        ast.parse(script.read_text(encoding="utf-8"), filename=str(script))
        checks.append({"label": f"syntax:{script.name}", "status": "pass", "error": ""})

    checks.append(expect_failure("tensor_shape", lambda: validate_tensor3(["1"] * 8)))
    checks.append(expect_failure("selection_count", lambda: assert_count(18, 19, "domains")))

    temp_path = root / f".self_test_{uuid.uuid4().hex}"
    temp_path.mkdir(parents=True)
    try:
        existing = temp_path / "existing.txt"
        existing.write_text("protected", encoding="ascii")
        checks.append(expect_failure("existing_target", lambda: protect_target(existing)))

        log = temp_path / "events.jsonl"
        append_event(log, "first", "pass")
        append_event(log, "second", "fail")
        lines = log.read_text(encoding="utf-8").splitlines()
        checks.append({
            "label": "append_only_events",
            "status": "pass" if len(lines) == 2 else "fail",
            "error": "",
        })

        evidence = {
            "gates": {},
            "storage": {"requested_points": 3, "stored_points": 1},
            "numerical_arrays": {"R": [0.1], "T": [0.9]},
            "results": {"nodes": {}},
            "artifacts": {"required": []},
        }
        errors = validate(evidence, temp_path)
        expected = (
            any(item.startswith("stored_point_mismatch") for item in errors)
            and any(item.startswith("missing_result_nodes") for item in errors)
        )
        checks.append({
            "label": "invalid_evidence_rejected",
            "status": "pass" if expected else "fail",
            "error": "" if expected else json.dumps(errors),
        })
    finally:
        shutil.rmtree(temp_path)

    status = "pass" if all(check["status"] == "pass" for check in checks) else "fail"
    print(json.dumps({"status": status, "checks": checks}, indent=2))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
