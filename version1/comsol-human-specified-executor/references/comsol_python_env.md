# COMSOL Python Environment

Treat every installation as machine-specific. Do not assume an operating
system, COMSOL version, install path, Python path, or licensed module.

Use the selected Python executable to run, from the skill directory:

```text
scripts/check_mph_backend.py --output <case-directory>/comsol_environment.json
scripts/check_mph_start.py
```

The environment report is not overwritten by default. Use a new path, or pass
`--force` only after confirming that replacement is intended.

The first script uses only the Python standard library unless `mph` is
available. It records the current platform, interpreter, package availability,
COMSOL discovery result, and path warnings. Keep this generated environment
file with the case, not inside the downloaded skill.

Resolve reported blockers before modeling. Install missing Python packages in a
user-approved environment; never modify the system Python silently. If startup
fails, inspect interpreter compatibility, COMSOL discovery, licensing, and path
encoding before changing session mode.

Prefer `mph` stand-alone mode when it works:

```python
import mph

mph.option("session", "stand-alone")
client = mph.start(cores=1)
```

Use another official COMSOL launch path only when required by that installation
and record the choice in `comsol_environment.json` or the execution report.
