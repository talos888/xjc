# Implementation Checklist

| ID | Human requirement | Source | Planned COMSOL API operation | Artifact or evidence | Status |
|---|---|---|---|---|---|
| R-001 | | | | | pending |

## File Safety

- [ ] All input paths resolved.
- [ ] Protected inputs remain read-only.
- [ ] Existing targets were inspected.
- [ ] Overwrite behavior matches user authorization.
- [ ] Existing source models use save-as unless exact replacement was authorized.
- [ ] Setup and solved models use distinct paths where practical.

## Pre-Run Static Review

- [ ] Every active requirement maps to code.
- [ ] No physical assumption was added silently.
- [ ] Units and expressions match the snapshot.
- [ ] Tags, selections, studies, datasets, and outputs are coherent.
- [ ] Failure stages and original COMSOL exceptions will be retained.

## Execution Evidence

- [ ] Geometry build status recorded.
- [ ] Mesh statistics recorded.
- [ ] Study and solver status recorded.
- [ ] Solution DOF recorded when applicable.
- [ ] Requested output values, units, shapes, and datasets recorded.
- [ ] Model and export save status recorded.
- [ ] Warnings, deviations, and mechanical fixes recorded.
