# COMSOL Run Plan Schema

Use JSON by default. YAML remains an optional compatibility format and requires
PyYAML. Keep the plan short and explicit so the runner can execute without
reloading the source paper.

## Top-level fields

- `simulation_id`: Stable file-safe identifier.
- `simulation_intent`: Optional planner handoff summary for review and reports.
- `assumptions`, `unresolved_questions`: Optional review notes copied into the
  run report.
- `save_policy`: Output paths and overwrite behavior.
- `parameters`: COMSOL global parameters, including units.
- `components`: Geometry, materials, physics, and mesh.
- `studies`: COMSOL study features to run.
- `variables`: Optional COMSOL variables.
- `couplings`: Optional component coupling operators such as integration
  operators. This is not COMSOL `Multiphysics`.
- `ports`, `scattering_boundaries`, `pml`: Optional Wave Optics helper sections.
- `solvers`: Optional explicit solver sequences.
- `tables`: Optional COMSOL result tables.
- `plots` or `results`: Optional plot groups. Use only when needed.
- `derived_values`: Optional numerical result features.
- `exports`: Optional COMSOL exports.
- `outputs`: Expressions to evaluate for numerical verification.

## Official name and API type

For each COMSOL object, provide either:

- `official_name`: A registered official COMSOL UI name from
  `scripts/comsol_api/registry.py`, or
- `api_type`: The COMSOL Java API type from COMSOL documentation, model history,
  or a verified existing model.

If the name is not registered and `api_type` is missing, the runner must fail.

## Component shape

```yaml
components:
  - tag: comp1
    dimension: 2
    geometry:
      tag: geom1
      features:
        - tag: r1
          official_name: Rectangle
          properties:
            size: ["1[um]", "2[um]"]
    selections:
      - tag: core_domains
        api_type: Explicit
        label: Core domains
        dimension: 2
        entities: [1]
    materials:
      - tag: mat1
        label: SiO2
        selection:
          named: core_domains
        property_groups:
          - tag: def
            properties:
              relpermittivity: 2.1316
    physics:
      - tag: ewfd
        official_name: Electromagnetic Waves, Frequency Domain
        api_type: <verified COMSOL Java API type>
        property_groups:
          - group: components
            properties:
              components: outofplane
        features: []
    mesh:
      tag: mesh1
      auto_size: 4
      require_nonzero_elements: true
      features:
        - tag: size1
          api_type: Size
          properties:
            hmax: 20[nm]
        - tag: ftri1
          api_type: FreeTri
```

## Properties

Most COMSOL feature settings can be written with `properties`:

```yaml
properties:
  expr: emw.normE
  descr: Field norm
```

Use `indexed_properties` when COMSOL model history or Java API examples require
`setIndex(...)` instead of `set(...)`, for example vector, table, or tensor-like
settings:

```yaml
indexed_properties:
  - property: expr
    index: 0
    value: emw.normE
  - property: descr
    index: 0
    value: Field norm
```

If COMSOL history shows two indexes, include `outer_index`:

```yaml
indexed_properties:
  - property: table
    outer_index: 0
    index: 1
    value: some_value
```

Use `property_groups` when COMSOL history shows `feature.prop("...")`. The
runner applies these to physics interfaces and other supported feature objects:

```yaml
property_groups:
  - group: components
    properties:
      components: outofplane
```

## Study shape

```yaml
studies:
  - tag: std1
    features:
      - tag: freq
        official_name: Frequency Domain
        properties:
          plist: c_const/lambda0
    run: true
```

## Output shape

```yaml
outputs:
  - name: field_norm
    type: stats
    expression: ewfd.normE
    dataset: dset1
    inner: last
    checks:
      count_gte: 1
      max_gt: 1e-12
```

Use `type: scalar` for scalar observables, `type: stats` for field/distribution
checks, and `type: raw` only for short scalar/vector probes. Set `limit` on raw
outputs to keep the JSON report small.

Supported checks include `count_gte`, `count_lte`, `min_gt`, `min_gte`,
`max_gt`, `max_gte`, `mean_gt`, `mean_gte`, `value_gt`, `value_gte`,
`*_lt`, and `*_lte`.

For models with multiple studies, solution datasets, time steps, or parameter
solutions, outputs may specify the `mph.Model.evaluate()` selectors `dataset`,
`inner`, `outer`, and `unit`. Do not rely on the default dataset when choosing
the wrong solution would change the result.

Complex-valued outputs must explicitly select `complex_mode`: `magnitude`,
`real`, `imag`, or `phase`. The runner fails instead of silently discarding the
imaginary part.

YAML booleans in `properties` and `indexed_properties` are encoded as COMSOL
`on`/`off`. Use explicit strings when a specific COMSOL property requires a
different representation.

## Verification

The runner verifies generic execution evidence after solving:

```yaml
verification:
  require_nonzero_dof: true
```

Each mesh defaults to `require_nonzero_elements: true` unless set to false. A
run should fail if required meshes have zero elements, required solution
sequences have zero DOF, or requested outputs evaluate to no finite values.

## Extended execution fields

Variables:

```yaml
variables:
  - tag: var1
    component: comp1
    expressions:
      field_energy_density: emw.normE^2
```

Coupling operators:

```yaml
couplings:
  - tag: intop_target
    component: comp1
    api_type: Integration
    geometry: geom1
    dimension: 2
    selection: {named: sel_target}
```

Use this section for COMSOL component coupling operators created through
`component.cpl()`, such as integration operators. Do not put COMSOL
`Multiphysics` nodes here.

Derived values and tables:

```yaml
tables:
  - tag: tbl1
    label: Derived values

derived_values:
  - tag: gev1
    api_type: EvalGlobal
    properties:
      expr: intop_target(field_expression)
    table: tbl1
    evaluate: true
```

Plots:

```yaml
plots:
  - tag: pg1
    api_type: PlotGroup2D
    label: Field norm
    features:
      - tag: surf1
        api_type: Surface
        properties:
          expr: emw.normE
```

Exports:

```yaml
exports:
  - tag: data1
    api_type: Data
    properties:
      filename: project/exports/result.csv
    run: true
```

Wave Optics helper sections:

```yaml
ports:
  - tag: port1
    component: comp1
    physics: ewfd
    selection: {named: input_boundary}
    properties:
      PortExcitation: 'on'

scattering_boundaries:
  - tag: sctr1
    component: comp1
    physics: ewfd
    selection: all
    properties:
      IncidentField: EField

pml:
  - tag: pml1
    component: comp1
    selection: {named: pml_domains}
```

## Lint before running

Run:

```powershell
.\.venv\Scripts\python.exe scripts\lint_plan.py --plan path\to\model_manifest.json
```

This catches JSON/YAML parse errors, missing `api_type` values, and common COMSOL
unit-expression quoting mistakes before COMSOL starts.

## Sweeps

Use COMSOL official study features for sweeps. For example, add a `Parametric
Sweep` study feature with explicit properties from model history or COMSOL docs.
The runner does not invent a separate sweep DSL.

## Explicit solvers

Use `solvers` only when the default `study.run()` sequence is not enough. Solver
features are built before the setup model is saved, then solver sequences with
`run: true` are executed after `_setup.mph` is saved.

If a solver sequence should be the only computation path for a study, set that
study's `run: false`:

```yaml
studies:
  - tag: std1
    features:
      - tag: freq
        official_name: Frequency Domain
        properties:
          plist: freq0
    run: false

solvers:
  - tag: sol1
    study: std1
    features:
      - tag: st1
        api_type: StudyStep
        properties:
          study: std1
          studystep: freq
    run: true
```
