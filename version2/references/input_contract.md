# Input Contract

## Blocking fields

Ask for a correction only when a missing value changes the physical model or prevents execution:

- geometry order, dimensions, and units;
- material assignment and required scalar/tensor components;
- physics interface and dimensionality;
- propagation direction, incidence condition, and polarization;
- boundary and port roles;
- study type and scan definition;
- required result quantities;
- target directory and overwrite policy.

Use explicit COMSOL defaults only when the user authorizes defaults or when the default is purely mechanical. Record every default in the snapshot.

## Requirement mapping

Each active human requirement needs:

- source wording;
- normalized value and unit;
- COMSOL API operation;
- verification evidence;
- final status.

Do not treat a generated script as evidence that COMSOL accepted the requirement.

## Clarification discipline

Ask one compact question containing only blockers. Do not ask about values already inferable without changing physics. A missing polarization in an electromagnetic port model is a blocker; a plot color is not.

## Corrections

The latest human correction overrides earlier text. Update the snapshot and checklist before execution.
