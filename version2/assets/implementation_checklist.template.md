# Implementation Checklist

| ID | Human requirement | COMSOL operation | Gate evidence | Status |
|---|---|---|---|---|
| R-001 | | | | pending |

## Gate Status

| Gate | Status | Evidence file or model node |
|---|---|---|
| intake | pending | |
| environment | pending | |
| capability | pending | |
| selection | pending | |
| build | pending | |
| mesh | pending | |
| single_point | pending | |
| storage | pending | |
| full_sweep | pending | |
| results | pending | |
| numerical_sanity | pending | |
| save | pending | |

## File Safety

- [ ] Protected inputs remain read-only.
- [ ] Existing targets were detected before writing.
- [ ] Setup and solved models use distinct paths.
- [ ] Append-only event log exists.

## Result Surface

- [ ] Native spectrum plot exists.
- [ ] Native field plot exists.
- [ ] Numerical evaluation and table exist.
- [ ] Dataset references and expressions are explicit.
- [ ] Export files are nonempty.
- [ ] Numerical values are omitted from chat unless explicitly requested.
