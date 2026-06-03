# COMSOL Run Plan Schema

Use YAML. Keep the plan short and explicit so the runner can execute without
reloading the source paper.

## Top-level fields

- `simulation_id`: Stable file-safe identifier.
- `save_policy`: Output paths and overwrite behavior.
- `parameters`: COMSOL global parameters, including units.
- `components`: Geometry, materials, physics, and mesh.
- `studies`: COMSOL study features to run.
- `results`: Optional plot groups. Use only when needed.
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
        features: []
    mesh:
      tag: mesh1
      auto_size: 4
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
```

Use `type: raw` only for short scalar/vector probes, and set `limit` to keep the
JSON report small.
