# Result Contract

Numerical results belong in COMSOL `Results` and artifact files by default.

## Required COMSOL nodes

For a spectral electromagnetic model:

- solved dataset;
- 1D global plot group for reflectance/transmittance or requested spectra;
- 2D plot group for the requested field expression;
- global evaluation nodes;
- result tables used by exports.

Every node needs a descriptive label and explicit dataset reference.

## Verification

Evidence must record:

- result node tags and labels;
- expressions and units;
- dataset tag;
- stored solution count;
- table row count;
- export paths and nonzero file sizes.

## Chat behavior

The default final response contains:

- execution status;
- model and artifact paths;
- failed gates or warnings;
- confirmation that Results nodes were created.

Do not paste spectra, peaks, or field values into chat unless the user explicitly requests them.

## Optional plotting dependencies

External plotting packages are optional. Their absence must not block creation of native COMSOL plots and tables.
