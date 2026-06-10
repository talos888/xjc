from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any


def path_warnings(path: Path) -> list[str]:
    text = str(path)
    warnings = []
    if any(ord(char) > 127 for char in text):
        warnings.append("path_contains_non_ascii_characters")
    if " " in text:
        warnings.append("path_contains_spaces")
    if "onedrive" in text.lower():
        warnings.append("path_is_inside_onedrive")
    return warnings


def inspect_mph() -> dict[str, Any]:
    if importlib.util.find_spec("mph") is None:
        return {"available": False, "error": "mph is not installed"}

    try:
        import mph

        return {
            "available": True,
            "module": str(Path(mph.__file__).resolve()),
            "backend": mph.discovery.backend(),
        }
    except Exception as error:
        return {
            "available": True,
            "error": f"{type(error).__name__}: {error}",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect the local COMSOL Python environment.")
    parser.add_argument("--output", type=Path, help="Optional JSON report path.")
    parser.add_argument("--force", action="store_true", help="Replace an existing report.")
    args = parser.parse_args()

    cwd = Path.cwd().resolve()
    executable = Path(sys.executable).resolve()
    report = {
        "platform": platform.platform(),
        "python": {
            "executable": str(executable),
            "version": platform.python_version(),
        },
        "working_directory": str(cwd),
        "path_warnings": {
            "python": path_warnings(executable),
            "working_directory": path_warnings(cwd),
        },
        "packages": {
            name: importlib.util.find_spec(name) is not None
            for name in ("mph", "jpype", "numpy")
        },
        "environment_hints": {
            key: value
            for key in ("COMSOL_ROOT", "COMSOL_HOME", "JAVA_HOME")
            if (value := os.environ.get(key))
        },
        "mph": inspect_mph(),
    }

    rendered = json.dumps(report, indent=2, default=str)
    print(rendered)
    if args.output:
        target = args.output.expanduser().resolve()
        if target.exists() and not args.force:
            print(f"report_not_written: target exists: {target}")
            return 2
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered + "\n", encoding="utf-8")
        print(f"report_written: {target}")

    return 0 if report["mph"].get("backend") else 1


if __name__ == "__main__":
    raise SystemExit(main())
