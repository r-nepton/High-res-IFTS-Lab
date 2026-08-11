# Calibration tables

Optional wavelength-dependent curves for matching a real telescope, optics, MKID, or sky continuum.

## Default behavior

`InstrumentConfig.calibration_profile = "parametric"` uses the built-in formulas. No tables are required.

## Using tables

Set `calibration_profile = "tables"` to load the packaged example CSVs, or set an individual field to a filename in this folder:

- `qe_curve`
- `re_curve`
- `mirror_reflectivity_curve` (single-bounce reflectivity)
- `optics_transmission_curve`
- `sky_continuum_curve` (photons s^-1 cm^-2 nm^-1 arcsec^-2)

## CSV format

```text
wavelength_nm,value
350.0,0.12
...
```

Wavelengths must be increasing. Values are linearly interpolated onto the simulator grid. Replace the example files with measured lab or site curves using the same columns; keep the filenames or point `InstrumentConfig` at your new filenames in this directory.
