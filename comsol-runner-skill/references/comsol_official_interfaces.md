# Registered COMSOL Official Interfaces

The registry is intentionally small. Add entries only after checking COMSOL
documentation, model history, or a successful local smoke run.

Current registry:

- Physics interfaces
  - `Coefficient Form PDE` -> `CoefficientFormPDE`
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

Wave Optics, RF, Semiconductor, and other module-specific interfaces should be
specified with explicit `api_type` in the plan until their Java API names have
been verified locally.
