from __future__ import annotations

import sys
import time
from contextlib import suppress
from pathlib import Path

import mph

from common import configure_mph, ensure_project_dirs, load_config, workspace


def build_simple_pde_model(model) -> None:
    java = model.java
    java.component().create("comp1", True)
    java.component("comp1").geom().create("geom1", 2)
    java.component("comp1").mesh().create("mesh1")

    java.component("comp1").geom("geom1").create("sq1", "Square")
    java.component("comp1").geom("geom1").feature("sq1").set("size", "L")
    java.component("comp1").geom("geom1").run()
    print("geometry_built:", True)

    java.component("comp1").physics().create("c", "CoefficientFormPDE", "geom1")
    java.component("comp1").physics("c").field("dimensionless").field("u")
    java.component("comp1").physics("c").field("dimensionless").component(["u"])
    java.component("comp1").physics("c").feature("cfeq1").set("c", "1")
    java.component("comp1").physics("c").feature("cfeq1").set("a", "0")
    java.component("comp1").physics("c").feature("cfeq1").set("f", "1")
    java.component("comp1").physics("c").create("dir1", "DirichletBoundary", 1)
    java.component("comp1").physics("c").feature("dir1").selection().all()
    java.component("comp1").physics("c").feature("dir1").set("r", "0")
    print("physics_created:", True)

    java.component("comp1").mesh("mesh1").autoMeshSize(5)
    java.component("comp1").mesh("mesh1").run()
    print("mesh_built:", True)

    java.study().create("std1")
    java.study("std1").create("stat", "Stationary")


def solve_simple_pde_model(model) -> None:
    java = model.java
    java.study("std1").run()
    print("study_solved:", True)

    java.result().create("pg_u", "PlotGroup2D")
    java.result("pg_u").label("Solution u - Surface")
    with suppress(Exception):
        java.result("pg_u").set("data", "dset1")
    java.result("pg_u").feature().create("surf_u", "Surface")
    java.result("pg_u").feature("surf_u").label("Surface u")
    java.result("pg_u").feature("surf_u").set("expr", "u")
    java.result("pg_u").run()
    print("surface_plot_created:", True)


def build_and_solve_simple_pde(model) -> None:
    build_simple_pde_model(model)
    solve_simple_pde_model(model)


def main() -> None:
    config = load_config()
    ensure_project_dirs(config)
    model_path = workspace(config) / "project/tests/test_minimal_simple-simulation.mph"
    model_name = "test_minimal_simple_simulation"

    print("python_executable:", sys.executable)
    print("target_model:", model_path)

    configure_mph(mph, config)
    started = time.perf_counter()
    client = None
    model = None
    try:
        client = mph.start(cores=int(config.get("cores", 1)))
        model = client.create(model_name)
        model.parameter("L", "1[mm]")
        build_and_solve_simple_pde(model)
        model.save(model_path)
        saved = Path(model_path).resolve()
        print("model_saved:", saved)
        print("file_size_bytes:", saved.stat().st_size)
        print("elapsed_seconds:", round(time.perf_counter() - started, 2))
    finally:
        if client is not None and model is not None:
            with suppress(Exception):
                client.remove(model)
        if client is not None:
            with suppress(Exception):
                client.disconnect()


if __name__ == "__main__":
    main()
