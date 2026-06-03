---
name: comsol-runner
description: Use when Codex needs to execute a COMSOL Multiphysics simulation plan through Python/mph using COMSOL official modules, physics interfaces, study types, feature API types, parameters, geometry, materials, solver runs, saved .mph files, and numerical verification. This is the runner/execution layer for literature-derived or planner-derived COMSOL plans; it does not classify papers or invent model families.
---

# COMSOL Runner

Control COMSOL through Python, `mph`, JPype, and COMSOL Java API calls. Treat this
skill as the execution layer of a larger workflow:

```text
human request / paper / image -> planner -> COMSOL run plan -> comsol-runner
```

Do not classify a paper into a model family here. Execute the confirmed plan.

## Default Approach

- Prefer `mph.option("session", "stand-alone")`.
- Do not use `comsolmphserver.exe` unless the user explicitly requests server mode.
- Use an ASCII-only workspace path with no spaces when possible.
- Avoid Desktop, OneDrive, and non-ASCII paths for active COMSOL automation.
- Do not rely on COMSOL GUI state to judge success; verify datasets, solutions, and evaluated values.
- For formal simulations, save both `_setup.mph` and `_solved.mph`.
- For quick tests, overwriting a test `.mph` is acceptable if the user agrees.
- Use COMSOL official names and Java API feature types. Do not invent virtual
  interfaces such as "waveguide_mode_2d" or "SHG interface" in the runner.
- If a plan uses an interface, study, or feature that is not registered in
  `scripts/comsol_api/registry.py`, require an explicit COMSOL Java `api_type`
  from the planner or stop with a clear error.

## Workflow

1. Read `references/interface_contract.md` when connecting this runner to an upstream planner.
2. Read `references/plan_schema.md` before editing or generating a run plan.
3. Run `scripts/check_backend.py` and `scripts/check_start.py` on a new machine.
4. Use `scripts/run_from_plan.py --plan <plan.yaml>` for planned COMSOL runs.
5. Use `scripts/verify_solution.py --model <file.mph>` to verify computed data.
6. Use `scripts/smoke_tests/coefficient_form_pde.py` only as an installation smoke test.
7. Export plots or tables only when requested or needed for visual debugging.
8. Report paths, file sizes, solver status, evaluated value ranges, warnings, and failures.

## Required Files

- `templates/runner_config.example.json`: copy to `runner_config.json` and edit for the local machine.
- `templates/run_plan.official.example.yaml`: copy or adapt for a COMSOL official API run.
- `templates/run_plan.smoke_test.yaml`: minimal installation test plan.
- `requirements.txt`: Python packages needed by runner scripts.

## References

- Read `references/interface_contract.md` for the planner-to-runner handoff.
- Read `references/plan_schema.md` for the supported run plan format.
- Read `references/comsol_official_interfaces.md` for registered official names and API types.
- Read `references/config.md` when setting up on a new machine.
- Read `references/file_naming.md` before saving formal simulations.
- Read `references/troubleshooting.md` when COMSOL starts but the GUI appears blank, paths fail, files lock, or JVM errors occur.

## Safety Rules

- Before running COMSOL, tell the user whether the action only checks availability, starts COMSOL, creates a model, solves a model, or overwrites a file.
- Do not overwrite formal simulation files unless the user explicitly requests it.
- If a file is locked by COMSOL GUI or another process, stop and ask the user to close it.
- If the GUI looks blank but solve logs succeeded, evaluate the target variable first; export a PNG only when visual confirmation is needed.
- Do not silently approximate missing official API types. Ask the planner/user for the COMSOL API type or inspect COMSOL documentation/model history first.
