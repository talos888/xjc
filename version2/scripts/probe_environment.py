from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import platform
import sys
import tempfile
from pathlib import Path
from typing import Any


def path_risks(path: Path) -> list[str]:
    text = str(path)
    risks = []
    if any(ord(char) > 127 for char in text):
        risks.append("non_ascii")
    if "onedrive" in text.lower():
        risks.append("onedrive")
    if " " in text:
        risks.append("spaces")
    return risks


def writable_probe(path: Path) -> dict[str, Any]:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".comsol_skill_write_probe"
        probe.write_text("ok", encoding="ascii")
        probe.unlink()
        return {"path": str(path.resolve()), "writable": True}
    except Exception as error:
        return {
            "path": str(path.resolve()),
            "writable": False,
            "error": f"{type(error).__name__}: {error}",
        }


def inspect_mph(start: bool, cores: int) -> dict[str, Any]:
    if importlib.util.find_spec("mph") is None:
        return {"available": False, "status": "mph_not_installed"}
    try:
        mph = importlib.import_module("mph")
        discovery = importlib.import_module("mph.discovery")
        result: dict[str, Any] = {
            "available": True,
            "module": str(Path(mph.__file__).resolve()),
            "backend": discovery.backend(),
        }
        if start:
            mph.option("session", "stand-alone")
            client = mph.start(cores=cores)
            result.update(
                status="client_started",
                version=str(getattr(client, "version", "unknown")),
                standalone=bool(getattr(client, "standalone", False)),
                module_count=len(client.modules()),
            )
        else:
            result["status"] = "backend_discovered"
        return result
    except Exception as error:
        return {
            "available": True,
            "status": "mph_probe_failed",
            "error": f"{type(error).__name__}: {error}",
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--case-dir", type=Path, default=Path.cwd())
    parser.add_argument("--temp-dir", type=Path)
    parser.add_argument("--start", action="store_true")
    parser.add_argument("--cores", type=int, default=1)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    if output.exists() and not args.force:
        raise FileExistsError(f"target_exists: {output}")
    temp_dir = (args.temp_dir or Path(tempfile.gettempdir())).expanduser().resolve()
    case_dir = args.case_dir.expanduser().resolve()
    report = {
        "platform": platform.platform(),
        "python": {
            "executable": str(Path(sys.executable).resolve()),
            "version": platform.python_version(),
            "path_risks": path_risks(Path(sys.executable).resolve()),
        },
        "case_directory": {
            **writable_probe(case_dir),
            "path_risks": path_risks(case_dir),
        },
        "temp_directory": {
            **writable_probe(temp_dir),
            "path_risks": path_risks(temp_dir),
        },
        "packages": {
            name: importlib.util.find_spec(name) is not None
            for name in ("mph", "jpype", "numpy", "matplotlib")
        },
        "environment_hints": {
            key: value
            for key in ("COMSOL_ROOT", "COMSOL_HOME", "JAVA_HOME")
            if (value := os.environ.get(key))
        },
        "mph": inspect_mph(args.start, args.cores),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    return 0 if report["mph"].get("status") in {"backend_discovered", "client_started"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
