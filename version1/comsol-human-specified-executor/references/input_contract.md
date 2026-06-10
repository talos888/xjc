# Input Contract

The input is executable when the supplied information uniquely determines the
requested model to the degree expected by the human.

## Sources

Record each effective source:

- conversation statements and later corrections;
- parameter or design files;
- existing `.mph` models;
- imported geometry, material, mesh, or measurement files;
- explicit permission to use named defaults or make named decisions.

Later user corrections override earlier statements. Do not silently resolve a
conflict between two still-active sources.

## Required Categories

Check the categories relevant to the requested model:

- destination directory, filenames, and overwrite policy;
- space dimension and geometry construction;
- selections or rules that identify domains, boundaries, edges, and points;
- material assignments and constitutive data;
- physics interfaces and couplings;
- initial, domain, boundary, edge, point, port, and source settings;
- mesh instructions or explicit authorization to use a COMSOL default mesh;
- study type, sweep values, solve sequence, and required solver settings;
- requested expressions, datasets, tables, plots, exports, and units;
- whether to build only, build and solve, or modify an existing model.

Not every category needs a value. It needs either an explicit instruction, an
explicitly authorized default, or a reason it is not applicable.

## Blocking Conditions

Stop and ask a focused question when:

- a required physical value is missing;
- geometry or selection instructions do not identify the intended entities;
- two active instructions conflict;
- a referenced file cannot be found or read;
- the requested target would overwrite a file without permission;
- an existing source model would be replaced without explicit, path-specific
  permission;
- the requested COMSOL module or feature appears unavailable;
- the requested output cannot be tied to a study, dataset, or expression.

Do not stop merely because the user used natural language instead of a schema.

## Execution Authorization

Treat phrases such as "create and run", "directly calculate", or equivalent as
authorization to execute once blocking issues are resolved. Treat requests to
"organize", "review", "show me first", or equivalent as a review gate.

Always freeze the effective input into `human_input_snapshot.md` before writing
the final model script, even when no extra confirmation is required.
