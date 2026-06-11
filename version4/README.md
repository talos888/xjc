# Version 4

Skill name: `comsol-general-executor-v4`

Version 4 hardens the general executor for formal simulations and
cross-physics reproduction work.

## Main Additions

- Supervised runs with explicit wall-clock limits
- Guarded changes to existing MPH files using inspection and source hashes
- Quantitative baseline comparisons for reproduction claims
- Stronger save/reload and stored-solution verification
- Native Results, arrays, plots, logs, manifests, models, and scores as artifacts
- Explicit separation between human-owned physics and executor-owned operations

## Tradeoff

The stronger evidence package can use more storage and generated text than a
one-off script, but it improves repeatability and failure diagnosis.

This version is retained for historical comparison; new users should install
`../final-version`.

## Install

```powershell
Copy-Item -Recurse .\version4 `
  "$HOME\.codex\skills\comsol-general-executor-v4"
```
