# Inspect Safe V0

Use `scripts/inspect_model.py` to inspect an existing `.mph` without modifying or saving it.

Required plan fields:

```yaml
job_id: inspect_existing_model
operation: inspect
source_model: project/models/source.mph
save_policy:
  output_dir: project/runs/inspect_existing_model
  overwrite: false
```

The command writes:

- `model_manifest.json`: exact source path and SHA-256, parameters, component/study/solution/dataset tags, mesh element counts, and solution state.
- `execution_report.json`: inspection status and a compact summary.

The manifest is a machine guard for a later Modify Safe V0 plan. Re-inspect after any external edit or save.
