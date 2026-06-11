from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OfficialType:
    official_name: str
    api_type: str
    category: str
    notes: str = ""


PHYSICS_INTERFACES: dict[str, OfficialType] = {
    "Coefficient Form PDE": OfficialType(
        official_name="Coefficient Form PDE",
        api_type="CoefficientFormPDE",
        category="Mathematics",
        notes="Smoke-test interface only unless selected by the planner.",
    ),
    "Electromagnetic Waves, Frequency Domain": OfficialType(
        official_name="Electromagnetic Waves, Frequency Domain",
        api_type="ElectromagneticWavesFrequencyDomain",
        category="Wave Optics",
        notes=(
            "Wave Optics frequency-domain interface. Use an explicit api_type "
            "for RF-style or version-specific alternatives."
        ),
    ),
}


STUDY_TYPES: dict[str, OfficialType] = {
    "Stationary": OfficialType("Stationary", "Stationary", "Study"),
    "Frequency Domain": OfficialType("Frequency Domain", "Frequency", "Study"),
    "Mode Analysis": OfficialType("Mode Analysis", "ModeAnalysis", "Study"),
    "Boundary Mode Analysis": OfficialType(
        "Boundary Mode Analysis", "BoundaryModeAnalysis", "Study"
    ),
    "Parametric Sweep": OfficialType("Parametric Sweep", "Parametric", "Study"),
    "Time Dependent": OfficialType("Time Dependent", "Transient", "Study"),
}


GEOMETRY_FEATURES: dict[str, OfficialType] = {
    "Square": OfficialType("Square", "Square", "Geometry"),
    "Rectangle": OfficialType("Rectangle", "Rectangle", "Geometry"),
    "Circle": OfficialType("Circle", "Circle", "Geometry"),
    "Block": OfficialType("Block", "Block", "Geometry"),
    "Sphere": OfficialType("Sphere", "Sphere", "Geometry"),
    "Cylinder": OfficialType("Cylinder", "Cylinder", "Geometry"),
    "Interval": OfficialType("Interval", "Interval", "Geometry"),
}


PHYSICS_FEATURES: dict[str, OfficialType] = {
    "Dirichlet Boundary": OfficialType(
        "Dirichlet Boundary", "DirichletBoundary", "Physics feature"
    ),
    "Port": OfficialType(
        "Port",
        "Port",
        "Wave Optics / RF physics feature",
        notes="Verified creatable on local COMSOL 6.4 probe.",
    ),
    "Scattering Boundary Condition": OfficialType(
        "Scattering Boundary Condition",
        "Scattering",
        "Wave Optics / RF physics feature",
        notes="Verified creatable on local COMSOL 6.4 probe.",
    ),
    "Periodic Condition": OfficialType(
        "Periodic Condition", "PeriodicCondition", "Physics feature"
    ),
}


def api_type_for(registry: dict[str, OfficialType], spec: dict, label: str) -> str:
    """Resolve a COMSOL Java API type from a registry or an explicit plan field."""
    api_type = spec.get("api_type")
    if api_type:
        return str(api_type)

    official_name = str(spec.get("official_name", "")).strip()
    if official_name in registry:
        return registry[official_name].api_type

    known = ", ".join(sorted(registry))
    raise ValueError(
        f"{label} requires an explicit COMSOL Java api_type or a registered "
        f"official_name. Got {official_name!r}. Known: {known}"
    )
