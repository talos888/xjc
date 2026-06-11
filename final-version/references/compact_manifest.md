# Compact Manifest V4

Use JSON by default. YAML is optional and requires PyYAML.

## Principle

The manifest describes a COMSOL feature graph:

- parameters;
- components;
- geometry features;
- named selections;
- materials and property groups;
- physics interfaces and features;
- mesh feature trees;
- studies and solvers;
- native Results, derived values, exports;
- execution and physical verification.

Use registered `official_name` values when available. Otherwise provide the explicit COMSOL Java `api_type`. A new model normally changes only JSON data.

## Typed values

Most values are COMSOL expression strings. Use typed wrappers only for overloaded Java calls:

```json
{"$bool": true}
{"$int": 2}
{"$double": 0.5}
{"$int_array": [1, 2, 3]}
{"$string_array": ["a", "b"]}
```

## Profiles

Profiles provide verified complete defaults for fragile reusable features:

- `comsol64.ewfd.wave-equation`
- `comsol64.ewfd.periodic-port`
- `comsol64.ewfd.floquet-periodic`

Manifest properties override profile defaults. Profiles are COMSOL-feature-specific, not model-specific.

## Named selection slots

Features such as periodic conditions and `CopyEdge` expose more than one selection:

```json
"named_selections": {
  "source": {"named": "sel_ymin"},
  "destination": {"named": "sel_ymax"}
}
```

## Verification

At minimum:

```json
"verification": {
  "require_nonzero_dof": true,
  "expected_stored_points": 3,
  "solvers": {
    "sol1": {"expected_stored_points": 3}
  },
  "required_result_tags": ["pg1"],
  "require_baseline_comparison": true,
  "reload_results": true
}
```

Store full numerical arrays in output artifacts, not the terminal report.

For an analytic or baseline comparison, evaluate the result and reference on the
same dataset:

```json
{
  "name": "field_error",
  "expression": "u",
  "reference_expression": "sin(pi*x/L)*sin(pi*y/L)",
  "comparison_metric": "relative_l2",
  "comparison_lte": 0.02,
  "artifact": "project/exports/u.csv"
}
```

Supported metrics are `relative_l2`, `rmse`, and `max_abs`. A failed limit stops
the run. The report keeps API, numerical, physical-validation, and reproduction
success as separate levels.

## Repetition macros

Use data macros to avoid repeating feature boilerplate. They are expanded before
linting and execution.

```json
{
  "features": [
    {
      "$for_each": {
        "as": "layer",
        "items": [
          {"tag": "r1", "pos": ["0", "0"], "size": ["1[um]", "2[um]"]},
          {"tag": "r2", "pos": ["1[um]", "0"], "size": ["3[um]", "2[um]"]}
        ],
        "template": {
          "tag": "${layer.tag}",
          "official_name": "Rectangle",
          "properties": {
            "pos": "${layer.pos}",
            "size": "${layer.size}"
          }
        }
      }
    }
  ]
}
```

`$repeat` accepts `count`, optional `start`, optional `as`, and `template`.
Use a whole-token value such as `"${layer.size}"` to preserve arrays or
objects. Embedded substitutions such as `"r${i}"` accept scalar values only.
