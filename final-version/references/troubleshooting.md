# Troubleshooting

## JVM path or library errors

Symptom:

```text
java.lang.UnsatisfiedLinkError: ... Can't find dependent libraries
```

Likely cause: active workspace path contains OneDrive, spaces, or non-ASCII
characters. Move the runner workspace to an ASCII-only local path.

## COMSOL GUI is blank

Do not assume the solve failed. COMSOL GUI may not refresh the active plot.

Verify through Python:

- list datasets
- list solutions
- evaluate a key expression
- optionally export a plot image if visual confirmation is needed

If finite values exist for the target expression, the solve has numerical
result data even if the GUI initially looks blank. Exporting an image is useful
for display debugging but is not required for validation.

## Locked `.mph` file

Symptom:

```text
Failed to save model. The file ... is locked by another program.
```

Close the file in COMSOL GUI, then retry. Do not force-delete or overwrite.

## Server message in stand-alone mode

The message below is usually harmless when using stand-alone mode:

```text
The client is not connected to a server.
```

It appears because the runner is not using `comsolmphserver.exe`.

## Backend found but start fails

If `check_backend.py` succeeds but `check_start.py` fails, inspect:

- path safety
- COMSOL license availability
- Java/JVM errors
- locked COMSOL processes
- permissions around the active workspace
# Runner-Specific Failures

- `requires an explicit COMSOL Java api_type`: the upstream planner used an
  official name that is not registered in `scripts/comsol_api/registry.py`.
  Confirm the API type from COMSOL documentation or model history, then add it
  to the plan or registry.
- `Expression ... evaluated to no finite values`: the study may not have solved,
  the expression may be wrong for the selected physics interface, or the dataset
  may not be active. Check solver status in COMSOL and verify expression names.
- `Undefined variable ewfd...` in Wave Optics: the local COMSOL variable prefix
  may be `emw` even if the physics tag is `ewfd`. Probe expressions such as
  `emw.normE`.
- YAML parser fails around values like `1[V/m]` or `-1190[nm]`: quote unit
  expressions inside flow lists, e.g. `['1[V/m]', '0', '0']`.
- `Refusing to overwrite existing file`: set `save_policy.overwrite: true` for
  tests only, or choose a new filename for formal simulations.
