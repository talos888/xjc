# COMSOL Runner Workflow

Use this workflow after the modeling intent and COMSOL official interface choices
are known.

1. Prepare a clean ASCII-only workspace.
2. Copy `templates/runner_config.example.json` to `runner_config.json`.
3. Create or reuse `.venv` and install `requirements.txt`.
4. Run `scripts/check_backend.py`.
5. Run `scripts/check_start.py`.
6. Run `scripts/check_environment.py` to verify Python dependencies.
7. For installation testing only, run `scripts/smoke_tests/coefficient_form_pde.py`.
8. For real work, create a compact JSON manifest matching `references/plan_schema.md`.
9. Run `scripts/lint_plan.py --plan <plan.yaml>`.
10. Run `scripts/run_from_plan.py --plan <plan.yaml>`.
11. Inspect the JSON run report.
12. Run `scripts/verify_solution.py` when extra verification is needed.

When a plan uses extended fields, read `references/execution_modules.md` before
editing the plan or runner modules.

For formal simulations, never overwrite the setup file after solving unless the
user explicitly asks. For tests, overwriting is acceptable when the user agrees.

The runner should not make literature-modeling decisions. If the plan lacks the
COMSOL official interface, study type, or feature API type needed for execution,
return to the planner step.

Keep virtual environments local to the machine. Commit `requirements.txt` and
runner scripts, but do not commit `.venv`, COMSOL installation paths, solved
model files, or machine-specific `runner_config.json`.
