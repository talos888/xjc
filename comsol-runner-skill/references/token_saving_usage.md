# Token-Saving Usage

The runner saves tokens by keeping repeated COMSOL mechanics in scripts:

- startup mode
- workspace layout
- setup/solved file saving
- official-name/API-type resolution
- generic geometry/material/physics/study creation
- numerical verification
- JSON run reports

For repeated literature simulations, do not resend the whole paper to the
runner. Send only a compact YAML plan that already includes the chosen COMSOL
official interface and the extracted modeling parameters.

Load references only as needed:

- `interface_contract.md` when connecting to upstream skills.
- `plan_schema.md` when creating or editing a plan.
- `comsol_official_interfaces.md` when checking registered API names.
- `troubleshooting.md` only when a run fails or COMSOL GUI state is confusing.

