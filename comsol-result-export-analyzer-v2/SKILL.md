---
name: comsol-result-export-analyzer-v2
description: Dehydrate solved COMSOL .mph results into lightweight reusable data packages without building, solving, modifying, displaying, or saving models. Use when Codex should export computed COMSOL data to CSV/NPZ plus manifest metadata, preserve Python analysis reuse, reduce repeated dependence on large .mph files, or run a post-solve file handoff from the COMSOL final executor skill.
---

# COMSOL Result Export Analyzer V2

Use this skill after a model has already been solved. Its purpose is to turn a
heavy `.mph` into a lightweight result package that can be analyzed later with
Python without reopening COMSOL.

## Workflow

1. Require an existing solved `.mph` or an existing `result_package/`.
2. Prefer a small `export_spec.json` produced by the modeling workflow.
3. Run `scripts/run_export_analysis.py --spec export_spec.json`.
4. Export requested COMSOL expressions to `data/*.csv` or `data/*.npz`.
5. Write `manifest.json`, `metadata.json`, `analysis/summary.json`, and
   `logs/export_log.txt`.
6. Optionally generate Python SVG plots from exported data.
7. Do not display images in chat unless the user asks separately.

## Environment

- Use `python scripts/self_test.py` to validate the deterministic package and
  analysis layer.
- CSV-only analysis uses Python standard library only.
- NPZ export requires `numpy`.
- COMSOL `.mph` export requires `mph` plus a working local COMSOL installation.

## Boundaries

- Do not create geometry, physics, mesh, studies, or solvers.
- Do not save changes back into the input `.mph`.
- Do not delete `.mph` files. Only record archive/delete suggestions in
  metadata when requested.
- Do not claim physical correctness, reproduction success, or conservation-law
  validity. Report only exported data statistics and requested derived features.
- If no solution exists, report `has_solution=false` and skip result exports.
- Keep raw arrays, logs, and summaries in files.
- Treat PlotGroup image export as optional diagnostics, not the main product.

## Spec

Use `assets/templates/export_spec.package.example.json` as the first template.
Read `references/export_schema.md` only when writing or debugging a spec.

Minimal command:

```powershell
python scripts/run_export_analysis.py --spec export_spec.json
```

Representative handoff:

```text
Final Skill produced model_solved.mph + final_run_manifest.json.
Now use this skill to export ewfd.Rorder_0, ewfd.Torder_0, ewfd.RTtotal,
and selected field arrays into a lightweight result_package for Python reuse.
```
