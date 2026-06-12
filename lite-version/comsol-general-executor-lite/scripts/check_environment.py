from __future__ import annotations

import argparse
import importlib
import json
import platform
import sys
from contextlib import suppress
from pathlib import Path
from typing import Any

from common import load_config


REQUIRED_PACKAGES = ("mph", "jpype", "numpy", "yaml")


def package_status(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    version = getattr(module, "__version__", None)
    return {"ok": True, "version": version}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="runner_config.json")
    parser.add_argument(
        "--start-comsol",
        action="store_true",
        help="Also start COMSOL through mph. This may take time and consume a license.",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    report: dict[str, Any] = {
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "config_path": str(Path(args.config).resolve()),
        "config_exists": Path(args.config).exists(),
        "session_mode": config.get("session_mode"),
        "workspace_root": config.get("workspace_root"),
        "project_root": config.get("project_root"),
        "cores": config.get("cores"),
        "packages": {name: package_status(name) for name in REQUIRED_PACKAGES},
    }

    report["ok"] = sys.version_info >= (3, 10) and all(
        item["ok"] for item in report["packages"].values()
    )

    if args.start_comsol:
        try:
            import mph

            mph.option("session", "stand-alone")
            client = mph.start(cores=int(config.get("cores", 1)))
            try:
                report["comsol_start"] = {
                    "ok": True,
                    "version": client.version(),
                    "modules": len(client.modules()),
                }
            finally:
                with suppress(Exception):
                    client.disconnect()
        except Exception as exc:
            report["ok"] = False
            report["comsol_start"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    print(json.dumps(report, indent=2))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

