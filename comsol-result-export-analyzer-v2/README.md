# COMSOL Result Export Analyzer V2

This skill exports already-computed COMSOL results into a lightweight
`result_package/` so later Python analysis can run without repeatedly opening a
large `.mph` file.

It is independent from the COMSOL final executor skill, but can be called after
that skill finishes solving a model.

## What It Does

- Reads a solved `.mph` model or existing CSV result package.
- Exports selected COMSOL expressions to `data/*.csv` or `data/*.npz`.
- Writes `manifest.json`, `metadata.json`, `analysis/summary.json`, and
  `logs/export_log.txt`.
- Optionally creates SVG plots from exported data.
- Does not build, solve, modify, save, or delete `.mph` files.

## Requirements

- CSV-only analysis: Python standard library.
- NPZ export: `numpy`.
- COMSOL `.mph` export: `mph` and a working local COMSOL installation.

## Basic Use

Start from the template:

```powershell
python scripts/run_export_analysis.py --spec assets/templates/export_spec.package.example.json
```

For a new model, copy the template and set:

- `model`: solved `.mph` path, or omit it when using `csv_inputs`.
- `csv_inputs`: existing CSV data for package-only analysis.
- `output_dir`: optional result package directory; defaults to `result_package`.
- `exports`: COMSOL expressions to export.
- `analysis.python_plots`: optional plots from exported data.

Detailed spec notes are in `references/export_schema.md`.

## Self Test

```powershell
python scripts/self_test.py
```

The self-test does not require COMSOL. It validates package creation, CSV
analysis, NPZ writing, schema notes, and basic safety checks.

## Output Layout

```text
result_package/
  manifest.json
  metadata.json
  data/
  analysis/
    summary.json
    summary.md
  plots/
  logs/
    export_log.txt
    run_status.json
```

