from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = {
    "workspace_root": ".",
    "project_root": "project",
    "cores": 1,
    "session_mode": "stand-alone",
}


def load_config(path: str | Path = "runner_config.json") -> dict[str, Any]:
    config = DEFAULT_CONFIG.copy()
    file = Path(path)
    if file.exists():
        config.update(json.loads(file.read_text(encoding="utf-8")))
    return config


def workspace(config: dict[str, Any]) -> Path:
    return Path(config.get("workspace_root", ".")).resolve()


def project_path(config: dict[str, Any], *parts: str) -> Path:
    return workspace(config) / config.get("project_root", "project") / Path(*parts)


def ensure_project_dirs(config: dict[str, Any]) -> None:
    root = workspace(config) / config.get("project_root", "project")
    for name in ("tests", "runs", "exports"):
        (root / name).mkdir(parents=True, exist_ok=True)


def configure_mph(mph_module, config: dict[str, Any]) -> None:
    if config.get("session_mode", "stand-alone") != "stand-alone":
        raise NotImplementedError("Only stand-alone mode is supported by these runner scripts.")
    mph_module.option("session", "stand-alone")
