# Registered COMSOL Official Interfaces

The registry is intentionally small. Add entries only after checking COMSOL
documentation, model history, or a successful local smoke run.

Current registry:

- Physics interfaces
  - `Coefficient Form PDE` -> `CoefficientFormPDE`
  - `Electromagnetic Waves, Frequency Domain` ->
    `ElectromagneticWavesFrequencyDomain`
- Study types
  - `Stationary` -> `Stationary`
  - `Frequency Domain` -> `Frequency`
  - `Mode Analysis` -> `ModeAnalysis`
  - `Boundary Mode Analysis` -> `BoundaryModeAnalysis`
  - `Parametric Sweep` -> `Parametric`
- Geometry features
  - `Square`, `Rectangle`, `Circle`, `Block`, `Sphere`, `Cylinder`
- Physics features
  - `Dirichlet Boundary` -> `DirichletBoundary`
  - `Port` -> `Port`
  - `Scattering Boundary Condition` -> `Scattering`
  - `Periodic Condition` -> `PeriodicCondition`

For formal work, prefer confirming API type names from a COMSOL model history or
official Java API documentation before adding them to the registry.

Wave Optics notes live in `references/wave_optics_api.md`. Use explicit
`api_type` values for RF-style or version-specific electromagnetic interfaces.
RF,
Semiconductor, Heat Transfer, Structural Mechanics, and other module-specific
interfaces should be specified with explicit `api_type` until verified locally.
