# Minimal Example

Conversation input:

> Build a 2D rectangle, 10 mm by 5 mm, with Heat Transfer in Solids. Set
> thermal conductivity to 2 W/(m*K), the left boundary to 350 K, and the right
> boundary to 300 K. Use a stationary study and save the model without running.

Snapshot excerpt:

```markdown
## Geometry
- 2D rectangle: 10[mm] x 5[mm]

## Materials
- Rectangle domain: k = 2[W/(m*K)]

## Physics
- Heat Transfer in Solids
- Left boundary: T = 350[K]
- Right boundary: T = 300[K]

## Study
- Stationary; build only
```

Checklist excerpt:

| ID | Human requirement | Planned COMSOL API operation | Status |
|---|---|---|---|
| R-001 | Create rectangle | Create and build rectangle geometry | pending |
| R-002 | Apply material | Set domain thermal conductivity | pending |
| R-003 | Set temperatures | Create two temperature boundary features | pending |

The example shows format and granularity only. Do not reuse its physics or
values in another case.
