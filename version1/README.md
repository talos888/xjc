# Version 1

Version 1 provides a portable `comsol-human-specified-executor` skill.

The human supplies and reviews the COMSOL model design. The agent translates those instructions into a case-specific Python or Java script, runs COMSOL, preserves artifacts, and verifies execution without inventing model physics.

## Install

Copy `comsol-human-specified-executor/` into the skills directory supported by your agent, preserving the complete folder structure.

## First Use

Run the bundled environment checks with the Python environment intended for COMSOL control:

```text
scripts/check_mph_backend.py --output <case-directory>/comsol_environment.json
scripts/check_mph_start.py
```

The skill does not assume a COMSOL version, installation path, Python path, operating system, or licensed module. Machine-specific findings are stored with the case rather than written into the skill.

## Scope

- Accepts model instructions from conversation, files, or both.
- Creates a frozen human-input snapshot and implementation checklist.
- Generates a case-specific COMSOL script rather than a universal model schema.
- Protects source models and existing outputs by default.
- Separates execution verification from physical validation.

This version does not automatically design the model, install COMSOL, configure licenses, or silently alter physics and solver settings to obtain convergence.
