# Version 3

Skill name: `comsol-general-executor-v3`

Version 3 changes the architecture from case-specific API scripts to a compact
manifest consumed by a general COMSOL feature-graph executor.

## Main Additions

- General JSON manifest and preprocessing layer
- Reusable geometry, materials, physics, studies, solver, Results, and export operations
- Domain profiles for fragile COMSOL API properties
- Existing-model inspection and guarded modification foundations
- Verification of geometry, mesh, solution size, sweep points, outputs, and reload persistence
- Manifest reuse to reduce repeated authoring

## Design Rule

A new model should normally require a new manifest, not a new helper. Core code
is changed only when a reusable COMSOL operation cannot be represented.

This version is retained for historical comparison; new users should install
`../final-version`.

## Install

```powershell
Copy-Item -Recurse .\version3 `
  "$HOME\.codex\skills\comsol-general-executor-v3"
```
