# COMSOL Runner Workflow

Use this workflow after the modeling intent and COMSOL official interface choices
are known.

1. Prepare a clean ASCII-only workspace.
2. Copy `templates/runner_config.example.json` to `runner_config.json`.
3. Create or reuse `.venv` and install `requirements.txt`.
4. Run `scripts/check_backend.py`.
5. Run `scripts/check_start.py`.
6. For installation testing only, run `scripts/smoke_tests/coefficient_form_pde.py`.
7. For real work, create a YAML plan matching `references/plan_schema.md`.
8. Run `scripts/run_from_plan.py --plan <plan.yaml>`.
9. Inspect the JSON run report.
10. Run `scripts/verify_solution.py` when extra verification is needed.

For formal simulations, never overwrite the setup file after solving unless the
user explicitly asks. For tests, overwriting is acceptable when the user agrees.

The runner should not make literature-modeling decisions. If the plan lacks the
COMSOL official interface, study type, or feature API type needed for execution,
return to the planner step.

