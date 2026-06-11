from __future__ import annotations

import argparse
from contextlib import suppress
from pathlib import Path

import numpy as np
import mph

from common import configure_mph, ensure_project_dirs, load_config, workspace


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Path to .mph model, relative to workspace or absolute.")
    parser.add_argument("--expr", default="u", help="Expression to evaluate and plot.")
    parser.add_argument("--output", required=True, help="PNG output path, relative to workspace or absolute.")
    args = parser.parse_args()

    config = load_config()
    ensure_project_dirs(config)
    root = workspace(config)
    model_path = Path(args.model)
    if not model_path.is_absolute():
        model_path = root / model_path
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = root / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    configure_mph(mph, config)
    client = mph.start(cores=int(config.get("cores", 1)))
    model = None
    try:
        model = client.load(model_path)
        print("model:", model.name())
        print("datasets:", model.datasets())
        print("plots:", model.plots())
        print("solutions:", model.solutions())

        values = np.asarray(model.evaluate(args.expr), dtype=float)
        print("eval_expression:", args.expr)
        print("eval_shape:", values.shape)
        print("eval_min:", float(np.nanmin(values)))
        print("eval_max:", float(np.nanmax(values)))
        print("eval_mean:", float(np.nanmean(values)))

        java = model.java
        with suppress(Exception):
            java.result().remove("pg_export")
        java.result().create("pg_export", "PlotGroup2D")
        java.result("pg_export").label(f"Exported {args.expr} - Surface")
        with suppress(Exception):
            java.result("pg_export").set("data", "dset1")
        java.result("pg_export").feature().create("surf_export", "Surface")
        java.result("pg_export").feature("surf_export").set("expr", args.expr)
        java.result("pg_export").run()

        with suppress(Exception):
            java.result().export().remove("img_export")
        java.result().export().create("img_export", "Image2D")
        java.result().export("img_export").set("plotgroup", "pg_export")
        java.result().export("img_export").set("pngfilename", str(output_path.resolve()))
        java.result().export("img_export").run()
        print("png_exported:", output_path.resolve())
        print("png_size_bytes:", output_path.stat().st_size)
    finally:
        if model is not None:
            with suppress(Exception):
                client.remove(model)
        with suppress(Exception):
            client.disconnect()


if __name__ == "__main__":
    main()
