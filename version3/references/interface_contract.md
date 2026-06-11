# Planner-to-Runner Interface Contract

The runner consumes a confirmed COMSOL run plan. It does not read papers,
classify structures, or decide which physics interface should be used.

Upstream planner responsibilities:

1. Extract the literature-derived geometry, material parameters, boundary
   conditions, study choice, sweeps, and outputs.
2. Choose COMSOL official modules, physics interfaces, study types, and feature
   API types.
3. Emit a compact JSON manifest matching `references/plan_schema.md`.
4. Mark uncertain assumptions explicitly in the plan or stop before runner use.
5. Prefer named selections for geometry-dependent materials and boundary
   conditions instead of relying on undocumented entity numbers in prose.
6. Include `simulation_intent`, `assumptions`, and `unresolved_questions` for
   literature-derived first-pass models so a successful run is not confused with
   a validated reproduction.

Runner responsibilities:

1. Start COMSOL through `mph` in stand-alone mode.
2. Create model objects from official COMSOL names and Java API types.
3. Save setup and solved `.mph` files.
4. Verify numerical outputs.
5. Fail clearly when an official name or API type is missing.
6. Keep run reports compact so future iterations can reuse them without loading
   full COMSOL model files or source papers.

Do not use invented runner-level model families as execution inputs. Terms like
"semiconductor device", "optical cavity", or "thermal actuator" may appear in
notes, but execution must resolve to COMSOL official interfaces and Java API
feature types.

If the user supplies only a paper or image and asks to run COMSOL, create or
request a reviewed modeling-parameter document and `model_manifest.json` before using
the runner. Do not continue debugging a plan whose simulation intent does not
match the corrected task.
