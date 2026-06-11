from __future__ import annotations

import argparse
import json
from contextlib import suppress
from pathlib import Path

import mph

from common import configure_mph, load_config


PHYSICS_CANDIDATES = {
    "Wave Optics frequency domain": "ElectromagneticWavesFrequencyDomain",
    "RF-style electromagnetic waves": "ElectromagneticWaves",
    "Electromagnetic waves transient": "ElectromagneticWavesTransient",
}

FEATURE_CANDIDATES = {
    "Port": "Port",
    "Scattering Boundary Condition": "Scattering",
    "Periodic Condition": "PeriodicCondition",
    "Perfect Electric Conductor": "PerfectElectricConductor",
    "Perfect Magnetic Conductor": "PerfectMagneticConductor",
    "Impedance Boundary Condition": "ImpedanceBoundary",
    "Transition Boundary Condition": "TransitionBoundaryCondition",
    "Surface Current Density": "SurfaceCurrentDensity",
    "Surface Magnetic Current Density": "SurfaceMagneticCurrentDensity",
    "Lumped Port": "LumpedPort",
    "Numeric Port": "NumericPort",
    "Diffraction Order": "DiffractionOrder",
    "Wave Equation, Electric": "WaveEquationElectric",
}


def try_create_feature(physics, tag: str, api_type: str) -> dict:
    try:
        physics.create(tag, api_type, 1)
        feature = physics.feature(tag)
        return {
            "ok": True,
            "api_type": api_type,
            "actual_type": str(feature.getType()),
            "properties": [str(item) for item in feature.properties()],
        }
    except Exception as exc:
        return {"ok": False, "api_type": api_type, "error": f"{type(exc).__name__}: {exc}"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="runner_config.json")
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    config = load_config(args.config)
    configure_mph(mph, config)
    client = mph.start(cores=int(config.get("cores", 1)))
    model = None
    report = {"physics": {}, "features": {}}
    try:
        model = client.create("probe_wave_optics_api")
        java = model.java
        java.component().create("comp1", True)
        java.component("comp1").geom().create("geom1", 2)
        geom = java.component("comp1").geom("geom1")
        geom.create("r1", "Rectangle")
        geom.feature("r1").set("size", ["1[um]", "1[um]"])
        geom.run()

        for index, (name, api_type) in enumerate(PHYSICS_CANDIDATES.items(), start=1):
            try:
                physics_tag = f"emw{index}"
                java.component("comp1").physics().create(physics_tag, api_type, "geom1")
                physics = java.component("comp1").physics(physics_tag)
                report["physics"][name] = {
                    "ok": True,
                    "api_type": api_type,
                    "default_features": [str(item) for item in physics.feature().tags()],
                    "properties": [str(item) for item in physics.properties()],
                }
                if api_type == "ElectromagneticWavesFrequencyDomain":
                    for feature_index, (feature_name, feature_type) in enumerate(
                        FEATURE_CANDIDATES.items(), start=1
                    ):
                        report["features"][feature_name] = try_create_feature(
                            physics, f"probe{feature_index}", feature_type
                        )
            except Exception as exc:
                report["physics"][name] = {
                    "ok": False,
                    "api_type": api_type,
                    "error": f"{type(exc).__name__}: {exc}",
                }
    finally:
        if model is not None:
            with suppress(Exception):
                client.remove(model)
        with suppress(Exception):
            client.disconnect()

    text = json.dumps(report, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
