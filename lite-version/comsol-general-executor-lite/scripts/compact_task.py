from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from api_cache import cache_identity, load_api_cache


TASK_SCHEMA = "comsol-lite-task-v1"
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


def require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a mapping")
    return value


def require_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    if float(value) <= 0:
        raise ValueError(f"{label} must be positive")
    return float(value)


def number_text(value: float | int) -> str:
    return str(int(value)) if float(value).is_integer() else str(value)


def normalize_output_dir(value: Any, simulation_id: str) -> str:
    raw = str(value or f"project/lite/{simulation_id}").strip().replace("\\", "/")
    path = Path(raw)
    if path.is_absolute() or not raw:
        raise ValueError("output_dir must be a nonempty path relative to workspace_root")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("output_dir must not contain empty, dot, or parent segments")
    return "/".join(path.parts)


def range_points(start: float, step: float, stop: float) -> int:
    if step <= 0 or stop < start:
        raise ValueError("range requires step > 0 and stop >= start")
    intervals = (stop - start) / step
    rounded = round(intervals)
    if abs(intervals - rounded) > 1e-9:
        raise ValueError("range stop must be reached by an integer number of steps")
    return int(rounded) + 1


def flatten_layers(items: list[Any]) -> list[dict[str, Any]]:
    layers: list[dict[str, Any]] = []
    for item_number, raw in enumerate(items, start=1):
        item = require_mapping(raw, f"layers[{item_number}]")
        if "sequence" in item:
            repeat = int(item.get("repeat", 1))
            if repeat <= 0:
                raise ValueError("layer repeat must be positive")
            sequence = item["sequence"]
            if not isinstance(sequence, list) or not sequence:
                raise ValueError("repeated layer sequence must be a nonempty list")
            for repeat_number in range(1, repeat + 1):
                for sequence_number, child_raw in enumerate(sequence, start=1):
                    child = deepcopy(
                        require_mapping(
                            child_raw,
                            f"layers[{item_number}].sequence[{sequence_number}]",
                        )
                    )
                    base = str(
                        child.get("name")
                        or child.get("material")
                        or f"layer{sequence_number}"
                    )
                    child["name"] = f"{base}_{repeat_number}"
                    layers.append(child)
        else:
            layers.append(deepcopy(item))
    if not layers:
        raise ValueError("layers must not be empty")
    return layers


def epsilon_tensor(material: dict[str, Any]) -> list[str]:
    refractive_index = material.get("n")
    if isinstance(refractive_index, (int, float, str)):
        diagonal = [str(refractive_index)] * 3
    elif isinstance(refractive_index, list) and len(refractive_index) == 3:
        diagonal = [str(value) for value in refractive_index]
    else:
        raise ValueError("material n must be a scalar or a three-item list")
    return [
        f"({diagonal[0]})^2",
        "0",
        "0",
        "0",
        f"({diagonal[1]})^2",
        "0",
        "0",
        "0",
        f"({diagonal[2]})^2",
    ]


def common_header(task: dict[str, Any], version: str) -> dict[str, Any]:
    simulation_id = str(task.get("id", "")).strip()
    if not SAFE_ID_RE.match(simulation_id):
        raise ValueError("id must be file-safe ASCII")
    output_dir = normalize_output_dir(task.get("output_dir"), simulation_id)
    return {
        "comsol_version": version,
        "api_cache_identity": cache_identity(version),
        "simulation_id": simulation_id,
        "simulation_intent": str(task.get("intent", "")),
        "assumptions": [str(item) for item in task.get("assumptions", [])],
        "unresolved_questions": [
            str(item) for item in task.get("unresolved_questions", [])
        ],
        "save_policy": {
            "setup_file": f"{output_dir}/{simulation_id}_setup.mph",
            "solved_file": f"{output_dir}/{simulation_id}_solved.mph",
            "report_file": f"{output_dir}/{simulation_id}_report.json",
            "event_file": f"{output_dir}/{simulation_id}_events.jsonl",
            "overwrite": bool(task.get("overwrite", False)),
        },
    }


def compile_layer_stack(task: dict[str, Any], version: str) -> dict[str, Any]:
    unit = str(task.get("length_unit", "nm"))
    width = require_number(task.get("width"), "width")
    layers = flatten_layers(task.get("layers", []))
    materials = require_mapping(task.get("materials"), "materials")
    background = str(task.get("background_material", "air"))
    if background not in materials:
        raise ValueError("background_material is absent from materials")

    geometry = []
    wave_features = [
        {
            "tag": "wee1",
            "existing": True,
            "profile": "comsol64.ewfd.wave-equation",
            "properties": {"epsilonr": epsilon_tensor(materials[background])},
        }
    ]
    x_position = 0.0
    for index, layer in enumerate(layers, start=1):
        thickness = require_number(layer.get("thickness"), f"layer {index} thickness")
        material_name = str(layer.get("material", "")).strip()
        if material_name not in materials:
            raise ValueError(f"layer {index} uses unknown material {material_name!r}")
        tag = f"r{index}"
        geometry.append(
            {
                "tag": tag,
                "official_name": "Rectangle",
                "label": str(layer.get("name", tag)),
                "properties": {
                    "pos": [f"{number_text(x_position)}[{unit}]", "0"],
                    "size": [f"{number_text(thickness)}[{unit}]", "wav"],
                    "selresult": True,
                },
            }
        )
        if material_name != background:
            wave_features.append(
                {
                    "tag": f"we_{index}",
                    "api_type": "WaveEquationElectric",
                    "dimension": 2,
                    "profile": "comsol64.ewfd.wave-equation",
                    "selection": {"named": f"geom1_{tag}_dom"},
                    "properties": {
                        "epsilonr": epsilon_tensor(materials[material_name])
                    },
                }
            )
        x_position += thickness

    excitation = task.get("excitation", {}) or {}
    e0 = excitation.get("E0", ["0", "1[V/m]", "0"])
    if not isinstance(e0, list) or len(e0) != 3:
        raise ValueError("excitation.E0 must contain three components")
    port_index = str(excitation.get("port_refractive_index", materials[background]["n"]))
    wave_features.extend(
        [
            {
                "tag": "port1",
                "official_name": "Port",
                "dimension": 1,
                "profile": "comsol64.ewfd.periodic-port",
                "selection": {"named": "sel_xmin"},
                "properties": {
                    "PortName": "1",
                    "PortExcitation": True,
                    "E0": [str(value) for value in e0],
                    "n": port_index,
                },
            },
            {
                "tag": "port2",
                "official_name": "Port",
                "dimension": 1,
                "profile": "comsol64.ewfd.periodic-port",
                "selection": {"named": "sel_xmax"},
                "properties": {
                    "PortName": "2",
                    "PortExcitation": False,
                    "E0": [str(value) for value in e0],
                    "n": port_index,
                },
            },
            {
                "tag": "pc1",
                "official_name": "Periodic Condition",
                "dimension": 1,
                "profile": "comsol64.ewfd.floquet-periodic",
                "selection": {"named": "sel_periodic"},
                "properties": {
                    "manualDestinationSelection": {"$bool": False},
                    "kFloquet": [
                        str(value)
                        for value in task.get("floquet_k", ["0", "0", "0"])
                    ],
                },
            },
        ]
    )

    sweep = require_mapping(task.get("wavelength_sweep"), "wavelength_sweep")
    start = require_number(sweep.get("start"), "wavelength_sweep.start")
    step = require_number(sweep.get("step"), "wavelength_sweep.step")
    stop = require_number(sweep.get("stop"), "wavelength_sweep.stop")
    count = range_points(start, step, stop)
    header = common_header(task, version)
    output_dir = normalize_output_dir(task.get("output_dir"), str(task["id"]))
    header.update(
        {
            "parameters": {
                "wav": f"{number_text(width)}[{unit}]",
                "Lx": f"{number_text(x_position)}[{unit}]",
            },
            "components": [
                {
                    "tag": "comp1",
                    "dimension": 2,
                    "geometry": {"tag": "geom1", "features": geometry},
                    "selections": [
                        {
                            "tag": "sel_xmin",
                            "api_type": "Box",
                            "dimension": 1,
                            "properties": {
                                "xmin": f"-1[{unit}]",
                                "xmax": f"1[{unit}]",
                                "ymin": f"-1[{unit}]",
                                "ymax": f"wav+1[{unit}]",
                                "condition": "inside",
                            },
                        },
                        {
                            "tag": "sel_xmax",
                            "api_type": "Box",
                            "dimension": 1,
                            "properties": {
                                "xmin": f"Lx-1[{unit}]",
                                "xmax": f"Lx+1[{unit}]",
                                "ymin": f"-1[{unit}]",
                                "ymax": f"wav+1[{unit}]",
                                "condition": "inside",
                            },
                        },
                        {
                            "tag": "sel_ymin",
                            "api_type": "Box",
                            "dimension": 1,
                            "properties": {
                                "xmin": f"-1[{unit}]",
                                "xmax": f"Lx+1[{unit}]",
                                "ymin": f"-1[{unit}]",
                                "ymax": f"1[{unit}]",
                                "condition": "inside",
                            },
                        },
                        {
                            "tag": "sel_ymax",
                            "api_type": "Box",
                            "dimension": 1,
                            "properties": {
                                "xmin": f"-1[{unit}]",
                                "xmax": f"Lx+1[{unit}]",
                                "ymin": f"wav-1[{unit}]",
                                "ymax": f"wav+1[{unit}]",
                                "condition": "inside",
                            },
                        },
                        {
                            "tag": "sel_periodic",
                            "api_type": "Union",
                            "dimension": 1,
                            "properties": {"input": ["sel_ymin", "sel_ymax"]},
                        },
                    ],
                    "materials": [],
                    "physics": [
                        {
                            "tag": "ewfd",
                            "official_name": "Electromagnetic Waves, Frequency Domain",
                            "features": wave_features,
                        }
                    ],
                    "mesh": {
                        "tag": "mesh1",
                        "auto_size": int(task.get("mesh_auto_size", 3)),
                        "run": True,
                    },
                }
            ],
            "studies": [
                {
                    "tag": "std1",
                    "features": [
                        {
                            "tag": "freq",
                            "official_name": "Frequency Domain",
                            "properties": {
                                "plist": (
                                    f"c_const/range({number_text(start)}[{unit}],"
                                    f"{number_text(step)}[{unit}],"
                                    f"{number_text(stop)}[{unit}])"
                                )
                            },
                        }
                    ],
                    "run": True,
                }
            ],
            "tables": [{"tag": "tbl_rt", "label": "Reflection and transmission"}],
            "derived_values": [
                {
                    "tag": "gev_rt",
                    "api_type": "EvalGlobal",
                    "label": "Reflection and transmission",
                    "properties": {
                        "expr": [
                            "ewfd.Rorder_0",
                            "ewfd.Torder_0",
                            "ewfd.RTtotal",
                        ]
                    },
                    "table": "tbl_rt",
                    "evaluate": True,
                }
            ],
            "plots": [
                {
                    "tag": "pg_norme",
                    "api_type": "PlotGroup2D",
                    "label": "normE field",
                    "features": [
                        {
                            "tag": "surf_norme",
                            "api_type": "Surface",
                            "properties": {"expr": "ewfd.normE"},
                        }
                    ],
                    "run": True,
                },
                {
                    "tag": "pg_rt",
                    "api_type": "PlotGroup1D",
                    "label": "Reflection and transmission spectra",
                    "features": [
                        {
                            "tag": "glob_rt",
                            "api_type": "Global",
                            "properties": {
                                "expr": ["ewfd.Rorder_0", "ewfd.Torder_0"]
                            },
                        }
                    ],
                    "run": True,
                },
            ],
            "outputs": [
                {
                    "name": "reflectance",
                    "expression": "ewfd.Rorder_0",
                    "artifact": f"{output_dir}/reflectance.csv",
                    "checks": {
                        "finite": True,
                        "count_gte": count,
                        "count_lte": count,
                        "min_gte": -1e-6,
                        "max_lte": 1.000001,
                    },
                },
                {
                    "name": "transmittance",
                    "expression": "ewfd.Torder_0",
                    "artifact": f"{output_dir}/transmittance.csv",
                    "checks": {
                        "finite": True,
                        "count_gte": count,
                        "count_lte": count,
                        "min_gte": -1e-6,
                        "max_lte": 1.000001,
                    },
                },
                {
                    "name": "energy_sum",
                    "expression": "ewfd.RTtotal",
                    "artifact": f"{output_dir}/energy_sum.csv",
                    "checks": {
                        "finite": True,
                        "count_gte": count,
                        "count_lte": count,
                        "min_gte": float(task.get("energy_min", 0.995)),
                        "max_lte": float(task.get("energy_max", 1.005)),
                    },
                },
                {
                    "name": "field_norm",
                    "expression": "ewfd.normE",
                    "type": "stats",
                    "checks": {"finite": True, "count_gte": 1},
                },
            ],
            "verification": {
                "require_nonzero_dof": True,
                "expected_stored_points": count,
                "required_result_tags": ["pg_norme", "pg_rt"],
                "required_table_tags": ["tbl_rt"],
                "required_numerical_tags": ["gev_rt"],
                "reload_results": True,
            },
        }
    )
    return header


def compile_diffusion(task: dict[str, Any], version: str) -> dict[str, Any]:
    length = str(task.get("length", "1[m]"))
    diffusivity = str(task.get("diffusivity", "1e-4[m^2/s]"))
    initial = str(task.get("initial", "sin(pi*x/L)"))
    exact = task.get("exact")
    time_range = require_mapping(task.get("time_range"), "time_range")
    start = float(time_range.get("start", 0))
    step = require_number(time_range.get("step"), "time_range.step")
    stop = float(time_range.get("stop"))
    count = range_points(start, step, stop)
    header = common_header(task, version)
    output_dir = normalize_output_dir(task.get("output_dir"), str(task["id"]))
    variables = []
    outputs: list[dict[str, Any]] = [
        {
            "name": "field",
            "expression": "u",
            "artifact": f"{output_dir}/field.csv",
            "checks": {"finite": True, "count_gte": 2},
        }
    ]
    verification: dict[str, Any] = {
        "require_nonzero_dof": True,
        "expected_stored_points": count,
        "required_result_tags": ["pg_field"],
        "reload_results": True,
    }
    if exact:
        variables.append(
            {
                "tag": "var1",
                "component": "comp1",
                "expressions": {"u_exact": str(exact)},
            }
        )
        outputs[0].update(
            {
                "reference_expression": "u_exact",
                "comparison_metric": str(task.get("comparison_metric", "relative_l2")),
                "comparison_lte": float(task.get("comparison_lte", 0.002)),
            }
        )
        verification["require_baseline_comparison"] = True
    mesh = require_mapping(task.get("mesh", {}), "mesh")
    header.update(
        {
            "parameters": {"L": length, "D": diffusivity},
            "components": [
                {
                    "tag": "comp1",
                    "dimension": 1,
                    "geometry": {
                        "tag": "geom1",
                        "features": [
                            {
                                "tag": "i1",
                                "official_name": "Interval",
                                "properties": {"p1": "0", "p2": "L"},
                            }
                        ],
                    },
                    "materials": [],
                    "physics": [
                        {
                            "tag": "pde",
                            "official_name": "Coefficient Form PDE",
                            "field": {
                                "tag": "dimensionless",
                                "name": "u",
                                "components": ["u"],
                            },
                            "features": [
                                {
                                    "tag": "cfeq1",
                                    "existing": True,
                                    "properties": {
                                        "c": "D",
                                        "a": "0",
                                        "da": "1",
                                        "f": "0",
                                    },
                                },
                                {
                                    "tag": "init1",
                                    "existing": True,
                                    "properties": {"u": initial},
                                },
                                {
                                    "tag": "dir1",
                                    "official_name": "Dirichlet Boundary",
                                    "dimension": 0,
                                    "selection": "all",
                                    "properties": {"r": str(task.get("boundary_value", "0"))},
                                },
                            ],
                        }
                    ],
                    "mesh": {
                        "tag": "mesh1",
                        "features": [
                            {
                                "tag": "size1",
                                "api_type": "Size",
                                "properties": {
                                    "custom": True,
                                    "hmax": str(mesh.get("hmax", "0.01[m]")),
                                    "hmin": str(mesh.get("hmin", "0.002[m]")),
                                    "hgrad": str(mesh.get("hgrad", "1.2")),
                                },
                            },
                            {
                                "tag": "edg1",
                                "api_type": "Edge",
                                "selection_dimension": 1,
                                "selection": "all",
                            },
                        ],
                        "run": True,
                    },
                }
            ],
            "variables": variables,
            "studies": [
                {
                    "tag": "std1",
                    "features": [
                        {
                            "tag": "time",
                            "official_name": "Time Dependent",
                            "properties": {
                                "tlist": (
                                    f"range({number_text(start)}[s],"
                                    f"{number_text(step)}[s],"
                                    f"{number_text(stop)}[s])"
                                ),
                                "rtol": str(task.get("relative_tolerance", "1e-5")),
                                "usertol": True,
                            },
                        }
                    ],
                    "run": True,
                }
            ],
            "plots": [
                {
                    "tag": "pg_field",
                    "api_type": "PlotGroup1D",
                    "label": "Diffusion field",
                    "features": [
                        {
                            "tag": "line_field",
                            "api_type": "LineGraph",
                            "properties": {"expr": "u"},
                        }
                    ],
                    "run": True,
                }
            ],
            "outputs": outputs,
            "verification": verification,
        }
    )
    return header


def compile_feature_graph(task: dict[str, Any], version: str) -> dict[str, Any]:
    manifest = deepcopy(require_mapping(task.get("manifest"), "manifest"))
    manifest["comsol_version"] = version
    manifest["api_cache_identity"] = cache_identity(version)
    if "simulation_id" not in manifest:
        manifest["simulation_id"] = str(task["id"])
    if "save_policy" not in manifest:
        output_dir = normalize_output_dir(task.get("output_dir"), str(task["id"]))
        manifest["save_policy"] = {
            "solved_file": f"{output_dir}/{task['id']}_solved.mph",
            "report_file": f"{output_dir}/{task['id']}_report.json",
            "event_file": f"{output_dir}/{task['id']}_events.jsonl",
            "overwrite": bool(task.get("overwrite", False)),
        }
    return manifest


COMPILERS = {
    "layer-stack-ewfd-2d": compile_layer_stack,
    "diffusion-1d": compile_diffusion,
    "feature-graph": compile_feature_graph,
}


def validate_profiles(manifest: dict[str, Any], version: str) -> None:
    available = load_api_cache(version)["profiles"]
    unknown: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            profile = value.get("profile")
            if profile and profile not in available:
                unknown.add(str(profile))
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(manifest)
    if unknown:
        raise ValueError(
            f"Unverified COMSOL {version} profiles: {', '.join(sorted(unknown))}"
        )


def compile_task(task: dict[str, Any]) -> dict[str, Any]:
    if task.get("schema") != TASK_SCHEMA:
        raise ValueError(f"schema must be {TASK_SCHEMA!r}")
    version = str(task.get("comsol_version", "6.4"))
    load_api_cache(version)
    template = str(task.get("template", "")).strip()
    if template not in COMPILERS:
        raise ValueError(
            f"template must be one of: {', '.join(sorted(COMPILERS))}"
        )
    if not SAFE_ID_RE.match(str(task.get("id", ""))):
        raise ValueError("id must be file-safe ASCII")
    manifest = COMPILERS[template](task, version)
    validate_profiles(manifest, version)
    return manifest


def load_task(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return require_mapping(value, "task")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    manifest = compile_task(load_task(Path(args.task)))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    compact_bytes = Path(args.task).stat().st_size
    manifest_bytes = output.stat().st_size
    print(
        json.dumps(
            {
                "status": "ok",
                "manifest": str(output.resolve()),
                "compact_bytes": compact_bytes,
                "manifest_bytes": manifest_bytes,
                "byte_ratio": round(compact_bytes / max(manifest_bytes, 1), 3),
            },
            ensure_ascii=True,
        )
    )


if __name__ == "__main__":
    main()
