# MKID-IFTS Instrument Simulator

Modular simulator for a high-resolution imaging Fourier transform spectrograph (IFTS) paired with energy-resolving MKIDs. The package implements the development plan as a Python package with source models, atmosphere and sky background, telescope throughput, interferogram generation, MKID order sorting, spectrum recovery, analytical SNR estimation, and a command-line exposure time calculator.

The repository still includes the original exploratory notebook, `ifts_mkid_sim.ipynb`, but the maintained simulator now lives in the `mkid_ifts_sim` package.

## Package Layout

```text
mkid_ifts_sim/
    __init__.py
    config.py
    source.py
    atmosphere.py
    sky_background.py
    telescope.py
    ifts.py
    mkid_detector.py
    order_sorting.py
    spectrum_recovery.py
    snr.py
    etc.py
    plotting.py
    data/templates/
tests/
```

## Features

- Native spectral grid in wavenumber with wavelength conversion only at user-facing boundaries.
- Source entry points for point-source magnitude plus spectral type, extended-source surface brightness plus template, or user-provided CSV/FITS spectra.
- Atmospheric transmission with airmass scaling and optical telluric features.
- Sky background with moon-dependent continuum, representative OH airglow structure, atomic airglow, and thermal tail.
- Telescope collecting area and mirror-coating throughput.
- Vectorized Michelson interferogram generation with dual-output handling and Poisson counting noise.
- MKID QE, energy-resolution scaling, dead time, and saturation checks.
- Hard-cut and probabilistic order-sorting models.
- FFT-based spectrum recovery, optional apodization, and broadband order stitching.
- Analytical SNR and ETC modes suitable for batch calculations and parameter sweeps.

## Installation

Use Python 3.10+.

```bash
pip install -e .[test]
```

Core dependencies:

- `numpy`
- `scipy`
- `matplotlib`
- `astropy`
- `PyYAML`

## Quick Start

### Python API

```python
from mkid_ifts_sim import InstrumentConfig, snr_from_time

config = InstrumentConfig()
source = {
    "mode": "point",
    "spectral_type": "stellar_g2v",
    "magnitude": 20.0,
    "band": "r",
}

result = snr_from_time(source, config, t_total_s=1800.0)
print(result.snr.max())
```

### Command-Line ETC

Create a request file such as:

```yaml
mode: snr_from_time
t_total_s: 1800
config:
  strategy: probabilistic
  moon_phase: new
source:
  mode: point
  spectral_type: stellar_g2v
  magnitude: 20.0
  band: r
```

Run:

```bash
mkid-ifts-etc request.yaml
```

Supported ETC modes:

- `snr_from_time`
- `time_from_snr`
- `optimize_config`

## Development Notes

- `config.py` contains the central `InstrumentConfig` dataclass used across the package.
- The analytical ETC path uses `source -> atmosphere -> sky -> telescope -> snr`.
- The interferometric path is implemented in modular pieces so full end-to-end simulations can be assembled in scripts or notebooks using `ifts.py`, `order_sorting.py`, and `spectrum_recovery.py`.
- The current sky model includes representative OH structure and a thermal continuum approximation; it is designed to be extensible with fuller tabulated site data later.

## Testing

Run the test suite with:

```bash
pytest
```

The tests cover:

- blackbody and redshift behavior
- atmospheric absorption structure
- interferogram and dual-output consistency
- MKID detector scaling and saturation
- order sorting limits
- FFT recovery and stitching utilities
- ETC smoke tests
