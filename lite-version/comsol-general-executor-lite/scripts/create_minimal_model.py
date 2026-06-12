from __future__ import annotations

import sys
import time
from contextlib import suppress
from pathlib import Path

import mph

from common import configure_mph, ensure_project_dirs, load_config, workspace


def main() -> None:
    config = load_config()
    ensure_project_dirs(config)
    model_path = workspace(config) / "project/tests/test_minimal_create-model.mph"
    model_name = "test_minimal_create_model"

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
        model.save(model_path)
        print("model_created:", model.name())
        print("parameter_L:", model.parameter("L"))
        print("model_saved:", model_path.resolve())
        print("file_size_bytes:", Path(model_path).stat().st_size)
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

