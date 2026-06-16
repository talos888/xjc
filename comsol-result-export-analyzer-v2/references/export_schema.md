# Result Package Export Spec Schema

The spec is JSON.

Input source:

- Provide either `model` or `csv_inputs`.
- Use `model` for solved COMSOL `.mph` export.
- Use `csv_inputs` with `skip_comsol=true` for package-only Python analysis
  without opening COMSOL.

Optional:

- `project_root`: base path for relative model/output paths.
- `output_dir`: result package directory. Defaults to `result_package`.
- `handoff_manifest`: optional manifest from the modeling skill.
- `title`: report title.
- `skip_comsol`: `true` to analyze existing CSV inputs without loading COMSOL.
- `exports`: list of expression export specs.
- `csv_inputs`: existing CSV series to analyze without COMSOL export.
- `analysis.basic_statistics`: write `analysis/summary.json`.
- `analysis.python_plots`: optional SVG plots from exported data.
- `plot_groups`: optional diagnostic image exports; not a required workflow.
- `cleanup_policy`: metadata only. Never delete `.mph` automatically.

Expression spec:

```json
{
  "name": "transmittance",
  "expr": "ewfd.Torder_0",
  "format": "csv",
  "axis": {"name": "wavelength_nm", "type": "linear", "start": 750, "step": 1, "unit": "nm"},
  "complex_mode": "magnitude"
}
```

Use `format: "csv"` for 1D series and `format: "npz"` for larger arrays or
complex-valued data. The package always writes:

```text
result_package/
  manifest.json
  metadata.json
  data/
  analysis/summary.json
  plots/
  logs/export_log.txt
```

Python plot spec:

```json
{
  "name": "rt_wavelength",
  "series": ["reflectance", "transmittance"],
  "x_label": "Wavelength (nm)",
  "y_label": "Power"
}
```

The analyzer reports min/max/mean, index of extrema, and x positions when an
axis is available. It does not decide whether the results are physically valid.

Axis warning: `model.evaluate(...)` values are flattened before export. A
linear `axis` is safe for true 1D sweeps, but can be physically misleading for
2D fields, nested sweeps, or multi-dimensional arrays. For those cases prefer
NPZ export and include explicit coordinate arrays or dataset-specific export
logic in a later workflow.

Dependencies:

- CSV-only package analysis: Python standard library.
- NPZ export: `numpy`.
- COMSOL `.mph` export: `mph` and a working local COMSOL installation.
