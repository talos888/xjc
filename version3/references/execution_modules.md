# Execution Modules

The runner executes plan vocabulary through small modules:

- `variables.py`: COMSOL variables.
- `executor.py`: components, geometry, selections, materials, physics features,
  mesh features, and studies.
- `couplings.py`: COMSOL component coupling operators such as integration
  operators. This module does not create COMSOL `Multiphysics` nodes.
- `wave_optics.py`: explicit Wave Optics helper sections for ports, scattering boundaries, and PML coordinate systems.
- `solvers.py`: explicit solver sequences when the default study solver is not
  enough. Solver features are built before setup save; `run: true` solvers run
  after setup save.
- `plots.py`: plot groups and result tables.
- `derived_values.py`: numerical features such as global evaluation and integrations.
- `exports.py`: COMSOL export features.
- `verification.py`: domain-neutral mesh and solution evidence checks.

These modules do not infer modeling intent. The planner must provide the COMSOL
official API types, selections, expressions, and properties.

Use `properties` for normal `feature.set(...)` settings. Use
`indexed_properties` only when COMSOL model history or official Java API examples
show `feature.setIndex(...)`.

If a module cannot express a needed COMSOL action, extend the module and the
schema rather than embedding one-off Java API calls in a prompt.

Run the pure-Python regression suite after changing shared execution behavior:

```powershell
python -m unittest discover -s tests -v
```
