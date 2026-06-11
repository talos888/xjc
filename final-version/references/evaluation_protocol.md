# Evaluation Protocol

Freeze this protocol before an A/B run.

## Isolation

- Record the exact task prompt and allowed source files.
- A no-skill arm may not read the skill, prior case artifacts, or prior reports.
- A skill arm may read only the task prompt, the installed skill, and declared public sources.
- Record SHA-256 for all allowed inputs and generated text artifacts.
- A contaminated arm is disqualified rather than rescored.

## Token accounting

The audit reports UTF-8 bytes, characters, lines, and a deterministic token
proxy. The proxy counts each CJK character, estimates Latin/digit runs by four
characters per token, and counts punctuation. It is not an API billing record.

Report:

- `task_cost`: prompt + generated plan/code + retry/error text + final report;
- `cold_start_cost`: task cost plus loaded skill instructions/references;
- `warm_repeat_cost`: changed manifest/diff + new report.

Use identical file categories and the same audit script for all arms.

## Completion rubric

| Category | Points |
|---|---:|
| Geometry and materials | 20 |
| Physics and boundary conditions | 20 |
| Mesh, study, and solver | 15 |
| Native Results and requested outputs | 15 |
| Numerical or baseline accuracy | 20 |
| Reproducibility and portability | 10 |

## Critical gates

A score of 95 or more requires all of:

- solved `.mph` exists and reloads;
- nonzero mesh and DOF;
- requested sweep/time points are stored;
- requested Results nodes and artifact arrays exist;
- all declared physical/baseline checks pass;
- no unapproved physics changes;
- allowed-input audit passes;
- another user can run from task-local inputs plus the portable skill.

## Score caps

- no solved model: maximum 35;
- zero/unverified mesh or DOF: maximum 25;
- missing requested Results or arrays: maximum 60;
- no quantitative check when one is available: maximum 80;
- unapproved physical substitution: maximum 70;
- failed save/reload verification: maximum 85;
- contaminated allowed-input set: disqualified.

Scores must cite machine-readable evidence. Do not award points for a claimed
feature that is absent from the saved model or report.
