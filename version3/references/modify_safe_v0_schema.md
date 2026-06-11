# Modify Safe V0

Modify Safe V0 changes parameters in an existing model, clears old solution data, solves explicit studies, verifies nonzero mesh elements and solution DOF, and saves to a different target file.

Supported operation:

```yaml
ops:
  - op: set_parameter
    name: n_defect
    expected_old_value: "2.15"
    value: "2.16"
```

Required guards:

- `source_model.expected_file_sha256` exactly matches the source file.
- The supplied inspection manifest matches the same path and SHA-256.
- Every parameter exists and its manifest and live values exactly match `expected_old_value`.
- `actions.clear_solution` is `true`.
- `actions.solve_studies` explicitly lists existing study tags.
- Source and target paths differ.
- Existing output files are refused unless `save_policy.overwrite` is `true`.

Unsupported in Safe V0: feature, property, selection, geometry, mesh, material, physics, study, solver, dataset, and result-tree edits.
