from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def validate_frontmatter() -> list[str]:
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    errors = []
    if not text.startswith("---\n"):
        errors.append("missing_frontmatter")
        return errors
    end = text.find("\n---\n", 4)
    header = text[4:end]
    if "name: comsol-general-executor-v3" not in header:
        errors.append("wrong_name")
    if "description:" not in header:
        errors.append("missing_description")
    return errors


def main() -> int:
    checks = []
    temp_root = ROOT / ".self_test_tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    test_env = {
        key: value
        for key, value in os.environ.items()
        if key.upper() not in {"TEMP", "TMP", "TMPDIR"}
    }
    test_env.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "TEMP": str(temp_root),
            "TMP": str(temp_root),
            "TMPDIR": str(temp_root),
        }
    )
    for path in sorted(SCRIPTS.rglob("*.py")):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    checks.append({"name": "python_syntax", "status": "pass"})

    frontmatter_errors = validate_frontmatter()
    checks.append(
        {
            "name": "frontmatter",
            "status": "pass" if not frontmatter_errors else "fail",
            "errors": frontmatter_errors,
        }
    )

    plan = ROOT / "assets" / "templates" / "coefficient-pde-smoke.json"
    lint = subprocess.run(
        [sys.executable, str(SCRIPTS / "lint_plan.py"), "--plan", str(plan)],
        capture_output=True,
        text=True,
        check=False,
    )
    checks.append(
        {
            "name": "json_manifest_lint",
            "status": "pass" if lint.returncode == 0 else "fail",
            "output": lint.stdout[-1000:],
        }
    )

    tests = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "run_unit_tests.py"),
            "--tests",
            str(SCRIPTS / "tests"),
            "--temp",
            str(temp_root),
        ],
        capture_output=True,
        text=True,
        check=False,
        env=test_env,
    )
    checks.append(
        {
            "name": "unit_tests",
            "status": "pass" if tests.returncode == 0 else "fail",
            "output": (tests.stdout + tests.stderr)[-2000:],
        }
    )
    status = "pass" if all(item["status"] == "pass" for item in checks) else "fail"
    print(json.dumps({"status": status, "checks": checks}, indent=2))
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
