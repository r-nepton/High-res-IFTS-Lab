# High-resolution IFTS + MKID Simulation

Simulation of a high-resolution imaging Fourier transform spectrometer (IFTS) with an MKID (microwave kinetic inductance detector) backend. The notebook implements a forward model from input spectra through throughput, interferogram formation, Poisson noise, and FFT reconstruction, plus an MKID order-edge ambiguity indicator and an SNR(λ) proxy via Monte Carlo.

## Contents

- **`ifts_mkid_sim.ipynb`** — Main simulation notebook (run cells in order).

## Requirements

- Python 3.8+
- NumPy
- Matplotlib

Install with:

```bash
pip install numpy matplotlib
```

## Notebook overview

| Cell | Description |
|------|-------------|
| 1 | Imports and small utilities (`trapz_int`, `gaussian`, `safe_div`) |
| 2 | `SimConfig` dataclass — wavelength band, MKID R, OPD scan, timing, telescope, two-port option |
| 3 | Wavelength grid and example target + sky spectra (flat continuum + Gaussian line; replace with real spectra) |
| 4 | Throughput blocks: atmosphere, telescope, IFTS optics, MKID QE → total throughput and detector-level target/sky |
| 5 | Asymmetric OPD grid (short negative side for phase, main positive scan), resolution proxy δσ |
| 6 | MKID order bins from R, order-edge ambiguity (“edge-risk”) map |
| 7 | Two-port IFTS forward model: interferograms from spectrum in wavenumber; plot i_plus / i_minus |
| 8 | Poisson noise on (difference-port) interferogram; FFT reconstruction; spectrum in σ and λ |
| 9 | SNR(λ) proxy via Monte Carlo; overlay scaled order-edge risk |

## Configuration (`SimConfig`)

Edit the defaults in **cell 2** to match your setup:

- **Wavelength**: `lam_min`, `lam_max`, `n_lam`
- **MKID**: `mkid_R` (~35–50)
- **OPD scan**: `opd_max`, `n_steps_total`, `frac_negative`
- **Timing**: `t_step`, `overhead_step`
- **Telescope**: `telescope_diam`, `pix_solid_angle`
- **Output**: `use_two_port` (recommended True)

## Usage

1. Open `ifts_mkid_sim.ipynb` in Jupyter or VS Code.
2. Run all cells in order (kernel must keep state between cells).
3. Adjust `SimConfig` and/or replace the example target/sky in cell 3 with your own spectra.
4. Optionally swap the placeholder throughput functions in cell 4 for real curves.

## Notes

- **Units**: Wavelength in meters; spectral densities in “photons / s / m² / m” at input (arbitrary scale). Throughput and detector rates are consistent with that.
- **Reconstruction**: Current FFT assumes approximately uniform OPD spacing; for strongly asymmetric or non-uniform OPD, consider an NUFFT later.
- **Two-port**: Using the difference port `0.5*(i_plus - i_minus)` removes DC and is recommended for normalization.

## Branch / push

To push this to a branch:

```bash
git checkout -b ifts-mkid-sim   # or your branch name
git add ifts_mkid_sim.ipynb README.md
git commit -m "Add IFTS+MKID simulation notebook and README"
git push -u origin ifts-mkid-sim
```
