from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / "api_cache"


def cache_path(version: str) -> Path:
    normalized = str(version).strip()
    if not normalized or any(char not in "0123456789." for char in normalized):
        raise ValueError(f"Invalid COMSOL version: {version!r}")
    return CACHE_DIR / f"comsol-{normalized}.json"


def load_api_cache(version: str = "6.4") -> dict[str, Any]:
    path = cache_path(version)
    if not path.is_file():
        raise FileNotFoundError(
            f"No verified API cache for COMSOL {version}: {path}. "
            "Run a disposable capability probe before adding one."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("cache_schema") != 1:
        raise ValueError(f"Unsupported API cache schema in {path}")
    if str(data.get("comsol_version")) != str(version):
        raise ValueError(f"API cache version mismatch in {path}")
    if not data.get("verified_on") or not data.get("verification_scope"):
        raise ValueError(f"API cache lacks verification provenance: {path}")
    return data


def cache_identity(version: str = "6.4") -> dict[str, Any]:
    path = cache_path(version)
    data = load_api_cache(version)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "version": data["comsol_version"],
        "verified_on": data["verified_on"],
        "sha256": digest,
        "path": str(path),
    }
