# 2D EWFD Periodic-Port API Notes

Use these patterns for reviewed 2D frequency-domain electromagnetic models. Probe the installed COMSOL version when a property is uncertain.

## Polarization

For an in-plane electric-field model:

```python
ewfd.prop("components").set("components", "inplane")
```

Set the port incident field explicitly, for example `[0, 1[V/m], 0]`. Do not infer polarization from propagation direction.

## Periodic source and destination

The periodic feature selection contains both periodic sides. The destination selection contains only the destination side:

```python
periodic.selection().named("sel_yperiodic")
periodic.set("manualDestinationSelection", True)
periodic.selection("destinationDomains").named("sel_ymax")
periodic.set("PeriodicType", "Floquet")
periodic.set("Floquet_source", "UserDefined")
periodic.set("kFloquet", ["0", "0", "0"])
```

Assert main and destination counts separately before solve.

## Boundary selections

For axis-aligned boundaries, component-level `Box` selections with `condition=inside` are more stable than coordinate guessing. Assert entity dimension 1 and expected counts.

## Periodic mesh

A robust 2D pattern is:

1. mesh the source periodic boundary;
2. copy the source edge mesh to the destination;
3. map the domains.

Verify nonzero elements after mesh. Do not assume equal global sizes imply matching periodic meshes.

## Anisotropic permittivity

Validate a full 3-by-3 row-major tensor before calling COMSOL. For an in-plane orthorhombic dielectric:

```text
[nx^2, 0, 0,
 0, ny^2, 0,
 0, 0, nz^2]
```

When the material read path does not reliably expose anisotropy to EWFD, use domain-specific `WaveEquationElectric` features with explicit user-defined relative permittivity. Record this as an implementation mechanism, not a changed material model.

## Sweep storage

When every scan point must remain accessible, use a direct frequency list in the frequency-domain study. After solve, verify:

- solution parameter count;
- global evaluation array length;
- exported table row count.

Do not accept a requested range expression as proof that all solutions were retained.
