---
name: comsol-human-specified-executor-v2
description: Execute a human-designed COMSOL model from reviewed geometry, materials, physics, boundary conditions, mesh, studies, solver settings, and output requirements. Use when Codex must create or modify a case-specific COMSOL Python or Java script, run COMSOL, create numerical and plot nodes under the COMSOL Results tree, export artifacts, verify stored solutions and numerical sanity, preserve an append-only audit trail, and report paths without dumping numerical results into chat.
---

# COMSOL Human-Specified Executor V2

Execute the model the human specified. Do not redesign its physics.

## Operating Contract

1. Capture the effective specification in `human_input_snapshot.md`.
2. Ask only for unresolved items that change the physics or make execution impossible.
3. Translate each requirement into `implementation_checklist.md`.
4. Run the gates below in order. Stop at the first failed gate and preserve evidence.
5. Put numerical outputs in the COMSOL `Results` tree and artifact files by default.
6. In chat, report status, warnings, and paths only. Show numerical values only when the user explicitly asks.
7. Never overwrite an input model or existing target without explicit authorization.

Read [references/input_contract.md](references/input_contract.md) before deciding whether the input is executable. For 2D EWFD periodic-port models, also read [references/ewfd_periodic_2d.md](references/ewfd_periodic_2d.md). Read [references/execution_gates.md](references/execution_gates.md) before running.

## Gates

Run these gates sequentially:

1. **Intake**: requirements, units, polarization, propagation direction, output paths, and overwrite policy are explicit.
2. **Environment**: interpreter, `mph`, `jpype`, COMSOL backend, temporary directory, and path risks are recorded.
3. **Capability**: uncertain COMSOL feature/property names are probed in a disposable model.
4. **Selection**: entity dimensions and expected counts match the model specification.
5. **Build**: geometry, materials, physics, and boundary conditions build without hidden fallbacks.
6. **Mesh**: mesh has nonzero elements and periodic source/destination discretizations are compatible.
7. **Single point**: one frequency or wavelength solves with nonzero DOF and finite requested outputs.
8. **Storage**: a three-point sweep retains three solutions and three result rows.
9. **Full sweep**: run the full scan once only after all earlier gates pass.
10. **Results**: requested plots, numerical evaluations, tables, datasets, and exports exist under `Results`.
11. **Numerical sanity**: requested conservation, bounds, shape, and baseline checks pass.
12. **Save**: setup model, solved model, evidence, event log, and exports are present and nonempty.

Use `scripts/probe_environment.py` for the environment gate, `scripts/validate_case_evidence.py` for post-run evidence checks, and `scripts/audit.py` for append-only events and protected-path checks.

## Implementation Rules

- Prefer `mph.option("session", "stand-alone")` on Windows unless the user requires another mode.
- Use explicit Java integer arrays for overloaded API calls; see `scripts/comsol_api.py`.
- Create named selections and assert dimensions/counts before assigning physics.
- Treat periodic source and destination selections as distinct objects.
- Validate anisotropic tensors before sending them to COMSOL.
- Use a direct frequency list when all scan points must remain in the solution.
- Verify stored parameter count from the solution, not only the requested range.
- Save a pre-solve model and a solved model to different paths where practical.
- Write `execution_events.jsonl` append-only; include stage, status, elapsed time, and original exception text.
- Keep plotting libraries optional. COMSOL Results nodes are the primary result surface.

## Required Result Surface

Unless the user requests otherwise, a solved model must contain:

- a 1D global plot or table for requested spectra;
- a 2D plot group for the requested field quantity;
- numerical evaluation nodes tied to the solved dataset;
- tables for exported global values;
- explicit labels, expressions, units, and dataset references.

Artifact exports complement the Results tree; they do not replace it.

## Failure Policy

Mechanical API corrections are allowed when they preserve the specification, for example overload typing, tag changes, or equivalent selection plumbing. Record them.

Do not silently change material tensors, boundary-condition semantics, polarization, dimensionality, mesh strategy, study type, or scan range. Stop and request review if such a change appears necessary.

See [references/error_taxonomy.md](references/error_taxonomy.md) for classification and [references/result_contract.md](references/result_contract.md) for result-tree requirements.

## Completion

Run:

```powershell
python scripts/validate_case_evidence.py --evidence case_evidence.json --case-dir .
```

Do not claim success unless required gates pass and the solved model plus requested result artifacts exist.
