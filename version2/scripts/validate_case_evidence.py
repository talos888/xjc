from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


REQUIRED_GATES = [
    "intake",
    "environment",
    "capability",
    "selection",
    "build",
    "mesh",
    "single_point",
    "storage",
    "full_sweep",
    "results",
    "numerical_sanity",
    "save",
]


def nonempty(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 0


def finite_sequence(values: list[Any]) -> bool:
    try:
        return all(math.isfinite(float(value)) for value in values)
    except (TypeError, ValueError):
        return False


def csv_data_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return max(0, sum(1 for _ in csv.reader(handle)) - 1)


def validate(evidence: dict[str, Any], case_dir: Path) -> list[str]:
    errors: list[str] = []
    gates = evidence.get("gates", {})
    for gate in REQUIRED_GATES:
        if gates.get(gate, {}).get("status") != "pass":
            errors.append(f"gate_not_passed:{gate}")

    storage = evidence.get("storage", {})
    requested = int(storage.get("requested_points", -1))
    stored = int(storage.get("stored_points", -2))
    if requested != stored:
        errors.append(f"stored_point_mismatch:{requested}:{stored}")

    for label, values in evidence.get("numerical_arrays", {}).items():
        if len(values) != requested:
            errors.append(f"array_length_mismatch:{label}:{len(values)}:{requested}")
        if not finite_sequence(values):
            errors.append(f"nonfinite_array:{label}")

    required_nodes = {"spectrum_plot", "field_plot", "spectrum_table", "spectrum_evaluation"}
    nodes = evidence.get("results", {}).get("nodes", {})
    missing_nodes = sorted(required_nodes - set(nodes))
    if missing_nodes:
        errors.append("missing_result_nodes:" + ",".join(missing_nodes))

    for relative in evidence.get("artifacts", {}).get("required", []):
        path = (case_dir / relative).resolve()
        if not nonempty(path):
            errors.append(f"missing_or_empty_artifact:{relative}")

    csv_rel = evidence.get("artifacts", {}).get("spectrum_csv")
    if csv_rel:
        path = (case_dir / csv_rel).resolve()
        if nonempty(path):
            rows = csv_data_rows(path)
            if rows != requested:
                errors.append(f"csv_row_mismatch:{rows}:{requested}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--case-dir", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
    errors = validate(evidence, args.case_dir.resolve())
    report = {"status": "pass" if not errors else "fail", "errors": errors}
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
