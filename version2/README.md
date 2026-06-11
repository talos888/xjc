# Version 2

Skill name: `comsol-human-specified-executor-v2`

Version 2 keeps the case-specific script approach of Version 1 and makes the
execution process auditable.

## Main Additions

- Sequential intake, environment, capability, selection, build, mesh, and solve gates
- Required native COMSOL Results nodes and artifact files
- Single-point and short-sweep checks before a full sweep
- Append-only evidence and structured error classification
- Validation helpers for saved case evidence

## Tradeoff

This version is readable and effective for one-off human-designed models, but it
still regenerates substantial case-specific API code. It is retained for
historical comparison; new users should install `../final-version`.

## Install

```powershell
Copy-Item -Recurse .\version2 `
  "$HOME\.codex\skills\comsol-human-specified-executor-v2"
```
