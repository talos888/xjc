---
name: comsol-general-executor-v4
description: Execute reviewed COMSOL model specifications or guarded changes to existing MPH models through compact manifests, supervised runs, native Results, quantitative baseline comparisons, and save/reload verification. Use for formal model construction, repeated variants, parameter sweeps, paper or benchmark reproduction, and auditable cross-physics work where the human owns the physical model and the executor must minimize repeated tokens without weakening correctness.
---

# COMSOL General Executor V4

Convert a human-reviewed physical specification into a reproducible COMSOL run. This skill is an execution and verification layer, not an autonomous model designer.

## Route The Task

- Use direct conversation for concepts, one-property diagnosis, or disposable examples.
- Use `inspect_model.py` for an existing `.mph`.
- Use guarded modification only after inspection and source SHA verification.
- Use a compact JSON manifest for a new model or repeatable rebuild.
- Use `run_supervised.py` for formal or potentially long runs.

## Required Workflow

1. Freeze confirmed inputs, assumptions, unresolved questions, and the reproduction target.
2. Ask only about missing choices that change physical meaning.
3. Author or update the manifest; prefer a diff for repeat runs.
4. Run `lint_plan.py` before COMSOL starts.
5. Probe only uncached COMSOL features or version-sensitive properties.
6. Run through `run_supervised.py` with an explicit wall-clock limit.
7. Require nonzero mesh and DOF, solver-specific stored points, finite outputs, native Results, and save/reload persistence.
8. For a claimed reproduction, compare outputs against a declared analytic, numerical, or inspected-model baseline and report the error metric.
9. Store arrays, plots, logs, manifests, models, and scores as artifacts. Chat output stays compact.

Read [references/compact_manifest.md](references/compact_manifest.md) when writing a manifest. Load only the requested domain profile. Unknown features may use explicit `api_type` and properties; never add a case-specific helper.

## Architecture Boundary

- `scripts/comsol_api/`: generic feature graph execution and verification.
- `references/profiles/`: complete profiles for fragile reusable COMSOL features.
- `assets/templates/`: compact examples, not model-specific truth.
- Case geometry, materials, equations, boundary conditions, solver choices, targets, and scoring belong outside the skill.

Add core code only for an operation that is reusable across models and cannot be represented by the feature graph. Do not add helpers for a paper, material, layer stack, or benchmark.

## Success Levels

Report these separately:

1. `api_success`: COMSOL accepted and ran the operations.
2. `numerical_success`: mesh, DOF, storage, finite outputs, and Results passed.
3. `physical_validation`: declared conservation, analytic, or baseline checks passed.
4. `reproduction_success`: the predeclared comparison score met its threshold.

Never promote a lower level into a higher one.

## Token Rules

- Prefer manifest diffs and reusable profiles.
- Do not regenerate or paste large API scripts in chat.
- Load references progressively.
- Put raw arrays and logs in files.
- A first unfamiliar model may cost more than direct conversation; optimize repeated project work, not every isolated prompt.

## Safety

- Never overwrite an input model or output without authorization.
- Stop on unknown references, unsupported properties, empty selections, zero mesh, zero DOF, missing stored points, nonfinite outputs, missing Results, failed baselines, or timeout.
- A supervisor may terminate only the process tree it created.
- Mechanical API fixes are allowed only when manifest semantics stay unchanged.
- Never tune physical or numerical parameters to match a target without recording and obtaining authorization.

## Entry Points

```powershell
python scripts/lint_plan.py --plan model_manifest.json
python scripts/run_supervised.py --plan model_manifest.json --config runner_config.json --timeout-seconds 1800
python scripts/self_test.py
```

For reproduction work, preserve the source, extraction notes, manifest, setup and solved models, Results, comparison artifacts, execution report, and score in one isolated case directory.
