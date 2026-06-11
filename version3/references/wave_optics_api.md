# Wave Optics API Notes

Use this reference when a plan uses Wave Optics or RF-style electromagnetic
interfaces. Keep execution plans based on COMSOL official names and Java API
types.

## Verified Locally

Verified on local COMSOL 6.4 during runner development:

- Physics interface
  - Wave Optics frequency domain:
    `ElectromagneticWavesFrequencyDomain`
  - `ElectromagneticWaves` may be valid for RF-style or version-specific
    models; require an explicit `api_type` instead of treating it as equivalent.
- Physics features
  - `Scattering Boundary Condition` -> `Scattering`
  - `Port` -> `Port`
- Scattering boundary `IncidentField` valid values observed:
  - `NoIncidentField`
  - `EField`
  - `HField`
  - `GaussianBeam`
- In local EWFD runs, evaluated field variables used the `emw` prefix:
  - `emw.normE`
  - `emw.Ez`

## Candidate Feature Probe List

The script `scripts/probe_wave_optics.py` can test common feature API types on a
new machine. Candidate feature API types include:

- Physics interfaces:
  - `ElectromagneticWavesFrequencyDomain`
  - `ElectromagneticWaves`
  - `ElectromagneticWavesTransient`

- `Port`
- `Scattering`
- `PeriodicCondition`
- `PerfectElectricConductor`
- `PerfectMagneticConductor`
- `ImpedanceBoundary`
- `TransitionBoundaryCondition`
- `SurfaceCurrentDensity`
- `SurfaceMagneticCurrentDensity`
- `LumpedPort`
- `NumericPort`
- `DiffractionOrder`
- `WaveEquationElectric`

Do not treat candidates as verified until the probe succeeds or a COMSOL model
history confirms the API type.

## Probe

```powershell
.\.venv\Scripts\python.exe scripts\probe_wave_optics.py --out wave_optics_probe.json
```

Use probe output to update a local plan with explicit `api_type` values. Commit
only generally useful verified registry additions, not machine-specific probe
logs.
