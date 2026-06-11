# Agent COMSOL Skills

A versioned set of Codex skills for building, running, and verifying COMSOL
models from human-reviewed physical specifications.

This repository records the evolution from case-specific script generation to
a reusable, manifest-driven COMSOL execution and verification layer. The human
or reviewed paper remains responsible for the physical model. The skill
translates that specification into COMSOL operations and preserves evidence.

## Versions

| Directory | Skill name | Status | Main purpose |
|---|---|---|---|
| `version1/` | `comsol-human-specified-executor` | Historical | Generate a readable case-specific COMSOL script from a complete human specification. |
| `version2/` | `comsol-human-specified-executor-v2` | Historical | Add execution gates, Results-tree requirements, evidence validation, and an error taxonomy. |
| `version3/` | `comsol-general-executor-v3` | Historical | Introduce a general feature-graph runner and compact manifests instead of model-specific helpers. |
| `version4/` | `comsol-general-executor-v4` | Historical | Add supervised runs, guarded existing-model changes, quantitative baselines, and stronger persistence checks. |
| `final-version/` | `comsol-general-executor-final` | **Recommended** | Add strict A/B audit rules, anti-inflation scoring gates, deterministic text-cost accounting, and portability fixes. |

The historical versions are retained for research and comparison. For normal
use, install only `final-version`.

## Final Architecture

```text
human or reviewed paper
        |
        v
reviewed physical specification
        |
        v
compact manifest or guarded model change
        |
        v
generic COMSOL Java API executor
        |
        v
mesh + solve + native Results + exports
        |
        v
quantitative checks + save/reload verification + audit report
```

Model-specific geometry, material values, equations, boundary conditions, and
targets belong in the case manifest. Core code is extended only for reusable
COMSOL operations that the feature graph cannot express.

## Requirements

- Windows with a licensed COMSOL Multiphysics installation
- A Python environment with `mph` and `jpype1`
- Codex or another agent runtime that supports local `SKILL.md` skills
- Access to the COMSOL modules required by the selected physics interfaces

COMSOL is proprietary software and is not included in this repository.

## Install The Recommended Version

Copy `final-version` into the Codex skills directory using the skill's declared
name:

```powershell
Copy-Item -Recurse .\final-version `
  "$HOME\.codex\skills\comsol-general-executor-final"
```

Restart or refresh the Codex session, then request a COMSOL task that matches
the description in `final-version/SKILL.md`.

## Basic Validation

From the installed skill directory:

```powershell
python .\scripts\self_test.py
```

The self-test checks Python syntax, skill frontmatter, manifest linting, and
unit tests. A passing self-test does not replace an actual COMSOL solve.

## Safety And Scope

- Do not treat a successful solve as proof that the physical model is correct.
- Do not silently invent missing physics or change settings to force convergence.
- Do not overwrite source MPH files without explicit authorization.
- Require nonzero mesh elements and solution degrees of freedom.
- For formal reproduction claims, require quantitative comparison against a
  declared analytic, numerical, experimental, or inspected-model baseline.
- Keep machine-specific paths, licenses, credentials, MPH files, and run logs
  outside the distributed skill.

## Repository Contents

Each version contains its own `SKILL.md`, scripts, references, templates, and a
short version README. Simulation cases and generated artifacts are intentionally
excluded so the skills remain reusable across users and models.

## License

No license is currently declared. Unless a license is added, the repository is
source-available for inspection but does not grant general reuse rights beyond
what copyright law otherwise permits.
