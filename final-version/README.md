# Final Version

Skill name: `comsol-general-executor-final`

This is the recommended production version.

It combines the general manifest executor from Version 3 with the supervised
execution and quantitative verification introduced in Version 4, then adds a
strict experiment-audit layer.

## Final Additions

- Frozen allowed-input lists for controlled A/B evaluation
- Anti-inflation scoring gates and explicit score caps
- Deterministic text-cost proxy with clear limits
- Relative audit paths resolved from the audit specification location
- Regression tests for audit portability
- Strong distinction between authored text, derived payloads, and generated reports

## Intended Role

The skill is a constrained COMSOL execution layer. It does not autonomously
choose the scientific model. A human or reviewed source supplies the physical
specification; the skill builds, runs, verifies, and reports it.

## Install

```powershell
Copy-Item -Recurse .\final-version `
  "$HOME\.codex\skills\comsol-general-executor-final"
```

## Validate

```powershell
Set-Location "$HOME\.codex\skills\comsol-general-executor-final"
python .\scripts\self_test.py
```

For formal runs, also verify the resulting MPH reloads, the mesh and solution
are nonempty, the requested sweep points are stored, and the declared
quantitative checks pass.
