from __future__ import annotations

import argparse
from contextlib import suppress
from pathlib import Path

import numpy as np
import mph

from common import configure_mph, load_config, workspace


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Path to .mph model, relative to workspace or absolute.")
    parser.add_argument("--expr", default="u", help="Expression to evaluate.")
    args = parser.parse_args()

    config = load_config()
    root = workspace(config)
    model_path = Path(args.model)
    if not model_path.is_absolute():
        model_path = root / model_path

    configure_mph(mph, config)
    client = mph.start(cores=int(config.get("cores", 1)))
    model = None
    try:
        model = client.load(model_path)
        print("model:", model.name())
        print("model_file:", model.file())
        print("datasets:", model.datasets())
        print("solutions:", model.solutions())
        print("plots:", model.plots())

        values = np.asarray(model.evaluate(args.expr), dtype=float)
        finite = values[np.isfinite(values)]
        print("eval_expression:", args.expr)
        print("eval_shape:", values.shape)
        print("finite_count:", int(finite.size))
        if finite.size == 0:
            raise RuntimeError(f'Expression "{args.expr}" evaluated to no finite values.')
        print("eval_min:", float(np.min(finite)))
        print("eval_max:", float(np.max(finite)))
        print("eval_mean:", float(np.mean(finite)))
        print("solution_verified:", True)
    finally:
        if model is not None:
            with suppress(Exception):
                client.remove(model)
        with suppress(Exception):
            client.disconnect()


if __name__ == "__main__":
    main()
