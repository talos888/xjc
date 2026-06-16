#!/usr/bin/env python
"""Fast self-test for the COMSOL result export/analyzer skill.

This test suite avoids requiring COMSOL. It validates the deterministic analysis
and reporting layer, plus basic skill packaging. Real COMSOL smoke tests should
be run separately when a solved .mph file is available.
"""

from __future__ import annotations

import ast
import json
import os
import shutil
import sys
import uuid
from pathlib import Path

sys.dont_write_bytecode = True

import run_export_analysis as rea


ROOT = Path(__file__).resolve().parents[1]


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def robust_rmtree(path: Path) -> None:
    def onexc(function, failed_path, excinfo):
        try:
            os.chmod(failed_path, 0o700)
            function(failed_path)
        except Exception:
            pass

    if not path.exists():
        return
    try:
        shutil.rmtree(path, onexc=onexc)
    except TypeError:
        shutil.rmtree(path, ignore_errors=True)


def check_python_syntax() -> None:
    for path in (ROOT / "scripts").glob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def check_skill_manifest() -> None:
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert_true("name: comsol-result-export-analyzer-v2" in skill, "SKILL.md missing expected name")
    assert_true("do not create geometry" in skill.lower(), "SKILL.md must state modeling boundary")
    assert_true("lightweight result package" in skill.lower(), "SKILL.md must state package purpose")
    assert_true("python scripts/self_test.py" in skill, "SKILL.md missing self-test command")
    assert_true("numpy" in skill and "mph" in skill, "SKILL.md missing dependency notes")
    assert_true((ROOT / "agents" / "openai.yaml").exists(), "agents/openai.yaml missing")
    schema = (ROOT / "references" / "export_schema.md").read_text(encoding="utf-8")
    assert_true("Provide either `model` or `csv_inputs`" in schema, "schema missing input-source rule")
    assert_true("Defaults to `result_package`" in schema, "schema missing output_dir default")
    assert_true("Axis warning" in schema, "schema missing axis warning")


def check_numeric_core(tmp: Path) -> None:
    axis = rea.linear_axis(750, 1, 351)
    assert_true(axis[0] == 750 and axis[-1] == 1100 and len(axis) == 351, "linear axis mismatch")
    series = rea.Series("T", axis[:4], [0.1, 0.5, 0.25, 0.9], unit="1", source="synthetic")
    summary = rea.summarize_series(series)
    assert_true(summary["argmax_x"] == 753, "argmax x mismatch")
    csv_path = tmp / "data" / "T.csv"
    rea.write_series_csv(csv_path, series)
    loaded = rea.read_series_csv(csv_path)
    assert_true(loaded.y == series.y, "CSV roundtrip mismatch")
    svg_path = tmp / "plots" / "T.svg"
    rea.write_svg_plot(svg_path, "Synthetic T", [series], "wavelength (nm)", "T")
    assert_true("<svg" in svg_path.read_text(encoding="utf-8"), "SVG plot was not written")


def check_csv_only_run(tmp: Path) -> None:
    csv_path = tmp / "input.csv"
    csv_path.write_text("index,x,y\n0,1,0.2\n1,2,0.4\n2,3,0.3\n", encoding="utf-8")
    spec = {
        "title": "CSV-only self test",
        "project_root": str(tmp),
        "skip_comsol": True,
        "output_dir": "out",
        "csv_inputs": [{"name": "probe", "path": "input.csv"}],
        "series_plots": [{"name": "probe_plot", "series": ["probe"], "x_label": "x", "y_label": "probe"}],
    }
    spec_path = tmp / "export_spec.json"
    spec_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    status = rea.run(spec_path)
    assert_true(status["ok"], "CSV-only run failed")
    assert_true(Path(status["package_files"]["manifest"]).exists(), "manifest missing")
    assert_true(Path(status["package_files"]["metadata"]).exists(), "metadata missing")
    assert_true(Path(status["package_files"]["summary"]).exists(), "summary missing")
    assert_true(status["series"][0]["argmax_x"] == 2.0, "CSV-only summary mismatch")
    report = Path(status["summary_markdown"]).read_text(encoding="utf-8")
    assert_true("does not build, modify, solve, save, or physically validate" in report, "scope disclaimer missing")
    manifest = json.loads(Path(status["package_files"]["manifest"]).read_text(encoding="utf-8"))
    assert_true(manifest["package_schema"] == "comsol-result-package-v2", "package schema mismatch")
    metadata = json.loads(Path(status["package_files"]["metadata"]).read_text(encoding="utf-8"))
    assert_true(metadata["can_analyze_without_mph"] is True, "package reuse flag missing")


def check_npz_writer(tmp: Path) -> None:
    series = rea.Series("field_flat", [0, 1, 2], [1.0, 2.0, 3.0], unit="V/m", source="synthetic")
    npz_path = tmp / "data" / "field_flat.npz"
    rea.write_series_npz(npz_path, series)
    assert_true(npz_path.exists() and npz_path.stat().st_size > 0, "NPZ export missing")


def check_alias_schema() -> None:
    raw = {
        "workspace_root": ".",
        "exports": {"plot_groups": "all", "expressions": [{"name": "T", "expression": "ewfd.Torder_0"}]},
        "analysis": {"x_axis": {"mode": "linear", "start": 1, "step": 2}, "series_plots": [{"name": "p"}]},
    }
    spec = rea.normalize_spec(raw)
    assert_true(spec["project_root"] == ".", "workspace_root alias failed")
    assert_true(spec["plot_groups"] == "all", "exports.plot_groups alias failed")
    assert_true(spec["exports"][0]["expr"] == "ewfd.Torder_0", "expression alias failed")
    assert_true(spec["x_axis"]["type"] == "linear", "x_axis mode alias failed")


def check_bom_json(tmp: Path) -> None:
    path = tmp / "bom.json"
    path.write_text('{"ok": true}', encoding="utf-8-sig")
    data = rea.load_json(path)
    assert_true(data["ok"] is True, "UTF-8 BOM JSON was not accepted")


def check_empty_source_fails(tmp: Path) -> None:
    spec = {"project_root": str(tmp), "skip_comsol": True, "output_dir": "empty"}
    spec_path = tmp / "empty_source.json"
    spec_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    status = rea.run(spec_path)
    assert_true(status["ok"] is False, "empty source should not report ok")
    assert_true(any("No data source provided" in w for w in status["warnings"]), "empty source warning missing")


def main() -> int:
    check_python_syntax()
    check_skill_manifest()
    check_alias_schema()
    tmp = ROOT / ".self_test_tmp" / uuid.uuid4().hex
    tmp.mkdir(parents=True)
    try:
        check_numeric_core(tmp)
        check_npz_writer(tmp)
        check_bom_json(tmp)
        check_csv_only_run(tmp)
        check_empty_source_fails(tmp)
    finally:
        robust_rmtree(tmp)
        parent = ROOT / ".self_test_tmp"
        try:
            parent.rmdir()
        except OSError:
            pass
    print("self_test: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
