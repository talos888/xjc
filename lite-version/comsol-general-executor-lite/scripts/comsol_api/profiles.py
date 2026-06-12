from __future__ import annotations

from copy import deepcopy
from typing import Any

from api_cache import load_api_cache


def profiles(version: str = "6.4") -> dict[str, dict[str, Any]]:
    return load_api_cache(version)["profiles"]


def apply_profile(spec: dict[str, Any]) -> dict[str, Any]:
    name = spec.get("profile")
    if not name:
        return spec
    version = str(spec.get("comsol_version", "6.4"))
    available = profiles(version)
    if name not in available:
        raise ValueError(
            f"Unknown or unverified COMSOL {version} profile: {name}"
        )
    merged = deepcopy(available[name])
    for key, value in spec.items():
        if key == "properties":
            merged.setdefault(key, {}).update(value or {})
        elif key in {"indexed_properties", "property_groups"}:
            merged.setdefault(key, []).extend(value or [])
        else:
            merged[key] = value
    merged.pop("comsol_version", None)
    return merged
