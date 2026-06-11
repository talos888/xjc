# COMSOL 6.4 EWFD Profiles

The profiles preserve the complete settings validated in v1.

## Wave equation

`comsol64.ewfd.wave-equation` explicitly sets:

- relative-permittivity displacement model;
- user-defined permittivity;
- user-defined relative permeability equal to 1;
- user-defined conductivity equal to 0 S/m.

The manifest must supply `epsilonr`.

## Periodic port

`comsol64.ewfd.periodic-port` explicitly sets:

- periodic port type;
- user-defined polarization;
- electric-field input;
- all incidence angles;
- user-defined refractive-index source.

The manifest must supply `PortName`, `PortExcitation`, `E0`, and `n`.

## Floquet periodic condition

`comsol64.ewfd.floquet-periodic` supplies manual destination selection, Floquet type, user-defined source, and zero default Floquet vector. Override `kFloquet` for nonzero phase.
