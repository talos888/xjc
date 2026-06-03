# COMSOL Runner Skill

Reusable Codex skill for executing confirmed COMSOL Multiphysics run plans with
Python, `mph`, JPype, and COMSOL Java API calls.

This runner is intentionally not a paper-understanding agent. Upstream planning
should decide the literature-derived geometry, materials, boundary conditions,
COMSOL official physics interface, study type, and output expressions. The
runner executes that plan, saves `.mph` files, and writes a compact JSON report.

## Requirements

- COMSOL Multiphysics installed and licensed on the local machine.
- Python 3.10+.
- Packages in `requirements.txt`.
- A local `runner_config.json` copied from `templates/runner_config.example.json`.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy templates\runner_config.example.json runner_config.json
```

Edit `runner_config.json` for your machine, then run a smoke test:

```powershell
.\.venv\Scripts\python.exe scripts\run_from_plan.py --plan templates\run_plan.smoke_test.yaml
```

For real simulations, create a plan following `references/plan_schema.md`.
Provide explicit COMSOL Java `api_type` values for module-specific interfaces
unless they are already registered in `scripts/comsol_api/registry.py`.

## What Not To Commit

Do not commit local config, generated `.mph` files, run reports, exports, or
private literature text. `.gitignore` is configured for the common generated
paths.

