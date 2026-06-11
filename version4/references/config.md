# Configuration

The runner should not hard-code user-specific paths.

Recommended local workspace:

```text
C:/Users/<user>/Documents/Codex/comsol-control
```

Avoid active simulation work in paths with spaces, OneDrive sync, Desktop sync,
or non-ASCII characters. JPype and the COMSOL JVM may fail or load libraries
incorrectly in such paths.

Copy:

```text
templates/runner_config.example.json
```

to:

```text
runner_config.json
```

Then edit `workspace_root`, `python_executable`, and `comsol_root`.

`runner_config.json` is machine-specific and should not be committed.
