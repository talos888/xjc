# Execution and Review Rules

## Implementation Review Before Run

Review the generated script statically against the input snapshot and checklist:

- every requested feature is represented;
- units and parameter expressions are preserved;
- geometry build order and selection references are coherent;
- materials are assigned to the intended entities;
- physics, boundary conditions, sources, and couplings match the specification;
- mesh, study, sweep, solver, dataset, and output tags are internally consistent;
- source files are opened read-only unless modification was requested;
- targets are distinct from protected inputs, and existing source models use
  save-as unless replacement was explicitly authorized for that exact path;
- intermediate and final saves occur at sensible failure boundaries;
- exceptions retain the failed stage and original COMSOL message.

This review checks implementation fidelity. It is not a numerical test.

## Execution Evidence

Collect evidence appropriate to the run:

- COMSOL session and required module availability;
- geometry build completion;
- nonempty mesh and mesh statistics;
- requested study or solver completion;
- nonzero solution degrees of freedom when applicable;
- requested expressions evaluated against the intended dataset;
- nonempty outputs with shape, unit, and basic finite-value checks;
- successful save of the expected `.mph` and exports;
- warnings, solver messages, and deviations from the snapshot.

Do not claim a result is physically correct from these checks.

## Allowed Mechanical Fixes

Fix without another approval when the intended model is unchanged:

- API spelling, property type, tag collision, or call ordering;
- path quoting, file encoding, serialization, or export formatting;
- selecting an equivalent official API call required by the installed version;
- correcting code that failed to apply an already specified value.

Record meaningful fixes in the execution report.

## Changes Requiring Human Approval

Pause before changing:

- geometry, material data, equations, physics, coupling, or boundary conditions;
- excitation magnitude, phase, polarization, frequency, wavelength, or sweep;
- mesh resolution or topology when it can affect the requested result;
- study type, solver tolerance, stabilization, scaling, continuation, or initial
  values;
- requested result expressions, normalization, dataset, or interpretation.

## Self-Review After Implementation

Perform a static self-review after creating or revising the case artifacts.
Report findings first, ordered by severity, with file and line references.
Inspect for:

- divergence from the frozen human input;
- hidden assumptions or unrecorded defaults;
- unsafe overwrite or path behavior;
- stale-solution or wrong-dataset risks;
- weak failure reporting;
- misleading success claims;
- unnecessary framework or abstraction growth.

Do not describe running tests when the user requested code review only.
