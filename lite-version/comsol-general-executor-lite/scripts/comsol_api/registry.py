from __future__ import annotations

from dataclasses import dataclass

from api_cache import load_api_cache


@dataclass(frozen=True)
class OfficialType:
    official_name: str
    api_type: str
    category: str
    notes: str = ""


def registry_for(
    section: str, category: str, version: str = "6.4"
) -> dict[str, OfficialType]:
    values = load_api_cache(version)["registry"][section]
    return {
        name: OfficialType(name, api_type, category)
        for name, api_type in values.items()
    }


def registries(version: str = "6.4") -> dict[str, dict[str, OfficialType]]:
    return {
        "physics_interfaces": registry_for("physics_interfaces", "Physics", version),
        "study_types": registry_for("study_types", "Study", version),
        "geometry_features": registry_for("geometry_features", "Geometry", version),
        "physics_features": registry_for(
            "physics_features", "Physics feature", version
        ),
    }


def api_type_for(registry: dict[str, OfficialType], spec: dict, label: str) -> str:
    api_type = spec.get("api_type")
    if api_type:
        return str(api_type)
    official_name = str(spec.get("official_name", "")).strip()
    if official_name in registry:
        return registry[official_name].api_type
    known = ", ".join(sorted(registry))
    raise ValueError(
        f"{label} requires an explicit COMSOL Java api_type or a verified "
        f"official_name. Got {official_name!r}. Known: {known}"
    )
