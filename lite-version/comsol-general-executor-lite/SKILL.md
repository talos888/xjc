---
name: comsol-general-executor-lite
description: Execute one-off or repeated COMSOL tasks with low conversation-token overhead using compact task JSON, versioned verified API caches, the general COMSOL runner, essential numerical gates, native Results, and concise status-only chat output. Use when the physical specification is already clear and full audit scoring is unnecessary; use the Final skill instead for formal paper reproduction, strict A/B evaluation, or high-stakes audited delivery.
---

# COMSOL General Executor Lite

Use Lite for a clear executable task. It is a compact route into the verified
general runner, not a weaker physics modeler.

1. Do not invent or silently change physics.
2. Ask only for missing choices that change physical meaning.
3. Write a compact task JSON; do not paste expanded manifests or raw arrays.
4. Require an exact COMSOL-version API cache for every requested profile.
5. Compile with `compact_task.py`; lint the generated manifest.
6. For costly runs, use `lite_run.py` with a timeout.
7. Require nonzero mesh and DOF, expected stored points, finite outputs, native
   Results, and saved-model reload.
8. Put details in files. Chat returns only status, failed gate, and paths.

Templates:

- `layer-stack-ewfd-2d`: repeated layered Wave Optics structures.
- `diffusion-1d`: one-dimensional transient diffusion with an optional exact solution.
- `feature-graph`: pass a compact or full generic manifest through the same runner.

Run:

```powershell
python scripts/compact_task.py --task task.json --output model_manifest.json
python scripts/lite_run.py --task task.json --config runner_config.json --timeout-seconds 1800
```

If a cache entry is missing, stop and create evidence with a disposable COMSOL
probe before updating `api_cache/`. Never guess a feature type or property.

Use `comsol-general-executor-final` when the task needs formal scoring, frozen
allowed-input audits, strict reproduction claims, or a complete evidence package.
