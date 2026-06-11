---
name: comsol-general-executor-v3
description: Compile reviewed human or paper-derived COMSOL specifications into compact JSON manifests, execute them through a general feature-based COMSOL Java API runner, create native Results nodes and artifact files, and verify geometry, mesh, solutions, stored sweep points, outputs, and save/reload persistence. Use for new COMSOL models across physics domains, repeated model variations, paper reproductions, or safe execution where token-efficient manifest reuse is preferred over regenerating case-specific API scripts.
---

# COMSOL General Executor V3

Use a compact manifest as the only executable model specification. Keep physics decisions with the human or reviewed paper extraction.

## Workflow

1. Normalize the request into `model_manifest.json`.
2. Ask only for missing decisions that change physics.
3. Run `scripts/lint_plan.py`.
4. Run environment and capability probes when the COMSOL version or requested feature is not cached.
5. Execute `scripts/run_from_plan.py`.
6. Require nonzero geometry/mesh/DOF, expected sweep storage, finite outputs, native Results nodes, and save/reload persistence.
7. Put numerical data in COMSOL Results and artifact files. Return only compact status and paths in chat unless values are explicitly requested.

Read [references/compact_manifest.md](references/compact_manifest.md) when authoring a plan. Read a domain profile only when that domain is requested. Unknown features may use explicit COMSOL `api_type` and properties; do not add a case-specific helper.

## Architecture Boundary

- `scripts/comsol_api/`: generic feature graph executor and verification.
- `references/profiles/`: verified property profiles for fragile COMSOL features.
- `assets/templates/`: compact example manifests.
- Case-specific geometry, materials, equations, boundary conditions, scans, and Results belong in the manifest.

Add code only for a new reusable COMSOL operation that the generic feature graph cannot express. Do not add helpers for new dimensions, layer counts, material values, or model layouts.

## Token Rules

- Prefer JSON manifest diffs for repeat runs.
- Do not paste generated Java/Python API code into chat.
- Do not load all references; open only the requested domain profile.
- Keep raw logs and numerical arrays in files.
- Print one compact execution JSON containing status, report path, model paths, and failed gate.

## Safety

- Never overwrite an input model or existing output without explicit authorization.
- Stop on unknown references, unsupported properties, empty selections, zero mesh, zero DOF, missing stored solutions, nonfinite outputs, or missing Results.
- Mechanical API fixes are allowed only when the manifest semantics remain unchanged.
- Do not tune physical or numerical parameters to match a paper without recording and obtaining authorization.

## Entry Points

```powershell
python scripts/lint_plan.py model_manifest.json
python scripts/run_from_plan.py --plan model_manifest.json --config runner_config.json
python scripts/self_test.py
```

For paper reproduction, preserve the paper, extraction notes, manifest, setup/solved models, Results, verification report, and comparison score in one isolated case directory.
