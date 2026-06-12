from __future__ import annotations

import json
from pathlib import Path
from typing import Any

def load_yaml_mapping(path: str | Path) -> dict[str, Any]:
    file = Path(path)
    if not file.exists():
        raise FileNotFoundError(file)
    text = file.read_text(encoding="utf-8")
    if file.suffix.lower() == ".json":
        value = json.loads(text)
    else:
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError(
                "YAML plans require PyYAML; use JSON for the zero-dependency path."
            ) from exc
        value = yaml.safe_load(text)
    if not isinstance(value, dict):
        raise ValueError(f"Plan must be a YAML mapping: {file}")
    return value


def load_json_mapping(path: str | Path) -> dict[str, Any]:
    file = Path(path)
    if not file.exists():
        raise FileNotFoundError(file)
    value = json.loads(file.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON must contain an object: {file}")
    return value


def load_mapping(path: str | Path) -> dict[str, Any]:
    file = Path(path)
    if file.suffix.lower() == ".json":
        return load_json_mapping(file)
    return load_yaml_mapping(file)


def resolve_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def require_nonempty_string(mapping: dict[str, Any], key: str) -> str:
    value = str(mapping.get(key, "")).strip()
    if not value:
        raise ValueError(f'Missing required non-empty field: "{key}"')
    return value


def prepare_output_files(
    root: Path,
    save_policy: dict[str, Any],
    job_id: str,
    default_model_name: str | None = None,
) -> dict[str, Path]:
    output_dir = resolve_path(root, save_policy.get("output_dir", f"project/runs/{job_id}"))
    names = {
        "report": save_policy.get("report_file", "execution_report.json"),
        "manifest": save_policy.get("manifest_file", "model_manifest.json"),
    }
    if default_model_name is not None:
        names["model"] = save_policy.get("model_file", default_model_name)
    files = {key: resolve_path(output_dir, value) for key, value in names.items()}
    overwrite = bool(save_policy.get("overwrite", False))
    for file in files.values():
        if file.exists() and not overwrite:
            raise FileExistsError(f"Refusing to overwrite existing file: {file}")
    output_dir.mkdir(parents=True, exist_ok=True)
    return files
