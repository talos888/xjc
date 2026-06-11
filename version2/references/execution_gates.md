# Execution Gates

Every gate writes a structured event and evidence payload.

| Gate | Minimum pass evidence |
|---|---|
| intake | no unresolved physical blockers |
| environment | usable Python, `mph`, `jpype`, COMSOL backend, writable case/temp paths |
| capability | all uncertain feature/property names accepted by a disposable model |
| selection | expected entity dimensions and counts |
| build | geometry/material/physics build status |
| mesh | positive element count; periodic boundary compatibility |
| single_point | nonzero DOF; finite requested outputs |
| storage | requested count equals stored solution count and evaluated row count |
| full_sweep | one completed full run after preceding gates |
| results | required plot groups, numerical nodes, tables, and exports |
| numerical_sanity | finite values and user-defined physical checks |
| save | nonempty setup/solved models and evidence artifacts |

## Escalation

Stop immediately when a gate fails. Preserve:

- original exception type and message;
- failed feature/tag/expression;
- last valid model path;
- gate evidence;
- elapsed time;
- whether retry would change physics.

Retry only mechanical failures. Physics-changing retries require human review.

## Efficiency

Use this order to avoid expensive invalid sweeps:

1. build only;
2. mesh only;
3. one point;
4. three points;
5. full sweep once.
