# COMSOL General Executor Lite

This release is the low-token companion to `final-version`.

- Skill package: `comsol-general-executor-lite/`
- Human guide: `HUMAN_GUIDE.md`
- Primary input: compact JSON using `comsol-lite-task-v1`
- Verified API cache: COMSOL 6.4
- Tested physics: 1D coefficient-form diffusion and 2D EWFD layered cavity

Lite compiles a short task into the mature general manifest runner. It keeps
nonzero mesh/DOF checks, expected solution-point checks, native Results,
quantitative outputs, saved-model reload, timeout supervision, and concise
status output.

Use `final-version` instead when a paper reproduction or formal comparison
requires a frozen evidence package, detailed scoring, or a full audit trail.

This folder is a release artifact. It is not automatically installed into the
local Codex skills directory.
