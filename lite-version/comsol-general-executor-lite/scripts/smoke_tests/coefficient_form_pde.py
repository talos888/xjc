from __future__ import annotations

import sys
import time
from contextlib import suppress
from pathlib import Path

import mph

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import configure_mph, ensure_project_dirs, load_config, workspace
from run_minimal_simulation import build_and_solve_simple_pde


def main() -> None:
    config = load_config()
    ensure_project_dirs(config)
    model_path = workspace(config) / "project/tests/test_smoke_coefficient-form-pde.mph"
    started = time.perf_counter()

    configure_mph(mph, config)
    client = None
    model = None
    try:
        client = mph.start(cores=int(config.get("cores", 1)))
        model = client.create("test_smoke_coefficient_form_pde")
        model.parameter("L", "1[mm]")
        build_and_solve_simple_pde(model)
        model.save(model_path)
        print("status: ok")
        print("python_executable:", sys.executable)
        print("model_saved:", model_path.resolve())
        print("file_size_bytes:", model_path.stat().st_size)
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

