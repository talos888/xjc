from __future__ import annotations

from copy import deepcopy
from typing import Any


PROFILES: dict[str, dict[str, Any]] = {
    "comsol64.ewfd.wave-equation": {
        "properties": {
            "DisplacementFieldModel": "RelativePermittivity",
            "epsilonr_mat": "userdef",
            "mur_mat": "userdef",
            "mur": "1",
            "sigma_mat": "userdef",
            "sigma": "0[S/m]",
        }
    },
    "comsol64.ewfd.periodic-port": {
        "properties": {
            "PortType": "Periodic",
            "Polarization": "UserDefined",
            "InputType": "E",
            "alpha_inc": "0",
            "alpha1_inc": "0",
            "alpha2_inc": "0",
            "n_mat": "UserDefined",
        }
    },
    "comsol64.ewfd.floquet-periodic": {
        "properties": {
            "manualDestinationSelection": {"$bool": True},
            "PeriodicType": "Floquet",
            "Floquet_source": "UserDefined",
            "kFloquet": ["0", "0", "0"],
        }
    },
}


def apply_profile(spec: dict[str, Any]) -> dict[str, Any]:
    name = spec.get("profile")
    if not name:
        return spec
    if name not in PROFILES:
        raise ValueError(f"Unknown COMSOL profile: {name}")
    merged = deepcopy(PROFILES[name])
    for key, value in spec.items():
        if key in {"properties"}:
            merged.setdefault(key, {}).update(value or {})
        elif key in {"indexed_properties", "property_groups"}:
            merged.setdefault(key, []).extend(value or [])
        else:
            merged[key] = value
    return merged
