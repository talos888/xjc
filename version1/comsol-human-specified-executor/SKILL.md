---
name: comsol-human-specified-executor
description: Execute a human-designed COMSOL model from complete instructions supplied in conversation, in one or more files, or through both. Use to translate reviewed geometry, materials, physics, boundary conditions, mesh, studies, solver settings, outputs, and paths into a case-specific Python or Java script; create files in the requested location; run COMSOL; preserve evidence; and report execution without inventing model physics.
---

# COMSOL Human-Specified Executor

Treat the human as the model designer and reviewer. Act as a precise programmer,
operator, and execution verifier. Create a case-specific script instead of
forcing the model into a universal modeling schema.

## Core Boundary

- Implement supplied modeling decisions faithfully.
- Do not choose the model family, physics interface, material law, excitation,
  boundary condition, mesh strategy, study type, or requested observable unless
  the human explicitly delegates that choice.
- Do not silently change physical or numerical settings to obtain convergence.
- Distinguish execution evidence from physical validation. A completed solve
  does not prove that the human-designed model represents reality.
- Prefer direct, readable COMSOL API code over new abstraction layers for a
  one-off model.

## Accept Inputs

Accept any combination of:

- instructions supplied directly in conversation;
- a user-provided Markdown, text, JSON, YAML, spreadsheet, document, image, or
  other parameter source;
- an existing model, data file, material table, geometry file, or result file.

Do not require the user to create a parameter file. For conversational or mixed
input, consolidate the effective instructions into `human_input_snapshot.md` in
the case directory before implementation. Use
`assets/human_input_snapshot.template.md` as a starting point.

Read `references/input_contract.md` when deciding whether the available
instructions are executable. Read `references/minimal_example.md` when an
example of the expected snapshot and checklist granularity would help.

## Execute

1. Resolve the requested case directory and every referenced input path.
2. Inspect existing files before writing. Preserve unrelated user files and do
   not overwrite an existing model, script, or result unless explicitly allowed.
3. Build `human_input_snapshot.md` from the effective conversation and file
   inputs. Mark sources and unresolved items.
4. Build `implementation_checklist.md` mapping each human requirement to the
   intended COMSOL API operation and output artifact. Use
   `assets/implementation_checklist.template.md`.
5. Stop before COMSOL execution if a required modeling decision is missing,
   contradictory, or ambiguous. Ask only for the blocking information.
6. If the instructions are complete and the user has requested execution,
   proceed without asking for a redundant confirmation. If the user requested a
   review first, present the snapshot and checklist and wait.
7. Create a case-specific Python or Java modeling script in the requested
   location. Keep units explicit and preserve supplied names where practical.
8. Before the first run on a machine, read
   `references/comsol_python_env.md`. Run the backend check with an output path
   for `<case-directory>/comsol_environment.json`, resolve reported blockers,
   then run `scripts/check_mph_start.py`. Use the detected Python and COMSOL
   environment in the case script; do not write machine-specific paths back
   into this skill.
9. Save an unsolved or setup model before a potentially long solve when
   practical. Save solved output to a distinct path. When modifying an existing
   `.mph`, preserve the source and save to a new target unless the user gives
   explicit, path-specific permission to replace that source.
10. Verify execution and write a concise report according to
    `references/execution_and_review.md`.

## Defaults

Classify every unspecified value before proceeding:

- **Physical/modeling default:** Stop unless the human explicitly authorizes AI
  selection. Examples: material values, geometry dimensions, boundary
  conditions, source polarization, sweep range, and target observable.
- **Numerical default:** Use a COMSOL-generated default sequence only when the
  human has authorized default numerical settings for the declared study, and
  record that authorization. Do not independently choose tolerances,
  stabilization, scaling, continuation, solver algorithms, or initial values.
- **Presentation default:** Choose nonphysical display details conservatively,
  such as plot styling, and record them only when they affect reproducibility.
- **Incidental implementation detail:** Choose conservatively and record it only
  when it affects reproducibility, such as generated feature tags or filenames.

Never use a default merely to make a failed model run.

## Failure Behavior

- Preserve the script, log, and latest valid intermediate model.
- Identify the exact failed stage: intake, path resolution, API construction,
  geometry, materials, physics, mesh, study, solve, evaluation, export, or save.
- Fix mechanical implementation errors when the human intent is unchanged.
- Request approval before changing model physics, mesh intent, study design,
  solver tolerances, stabilization, or convergence strategy.
- Do not report success from process exit alone.

## Output

Use the user-specified names and locations. When none are specified, keep all
new artifacts in one clearly named case directory and avoid existing files.
Normally produce:

- `human_input_snapshot.md`;
- `implementation_checklist.md`;
- a case-specific modeling script;
- setup and solved `.mph` files when the run reaches those stages;
- requested numerical data and plots;
- raw or captured execution logs;
- `execution_report.md` or `execution_report.json`.

Do not add a generic Runner, MCP server, or universal plan schema as part of a
case unless the user separately requests that architecture.
