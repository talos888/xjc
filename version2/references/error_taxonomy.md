# Error Taxonomy

Classify each failure before retrying.

| Class | Examples | Default action |
|---|---|---|
| input_blocker | missing polarization, ambiguous layer order | ask only for the blocker |
| environment | missing `mph`, unwritable temp directory | repair environment or stop |
| api_capability | rejected feature/property name | probe disposable model |
| selection | wrong entity dimension or count | stop before physics assignment |
| build | geometry/material/physics build exception | preserve setup model and exception |
| mesh | zero elements, periodic mismatch | stop before solve |
| solver | singularity, convergence, memory | preserve solver log; no physics changes |
| storage | requested points not retained | correct study/solver storage mechanism |
| results | missing dataset/plot/table/export | repair result surface without re-solving when possible |
| numerical | nonfinite values, failed conservation/bounds | mark run invalid |
| file_safety | target exists, protected input mutation | stop unless authorized |

Record whether a proposed correction is mechanical or physics-changing.
