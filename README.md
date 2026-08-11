# MKID-IFTS Instrument Simulator

Python package and planning tools for a high-resolution imaging Fourier transform spectrograph (IFTS) with energy-resolving microwave kinetic inductance detectors (MKIDs). The project models the path from astrophysical source to recovered spectrum and SNR, including filterless order sorting, analytical exposure-time estimation, and an interactive web calculator.

**Principal investigator:** Dr. Laurie Rousseau-Nepton (High-Resolution IFTS Lab)

## Live demo

| Resource | URL |
|----------|-----|
| Web ETC | [https://mkid-ifts.shayaanauqil.ca/](https://mkid-ifts.shayaanauqil.ca/) |
| API (Render) | [https://mkid-ifts-api.onrender.com/health](https://mkid-ifts-api.onrender.com/health) |
| Source repository | [https://github.com/r-nepton/High-res-IFTS-Lab](https://github.com/r-nepton/High-res-IFTS-Lab) |

The Python package is **0.2.0**. The interactive site is **Web ETC v1.1**, built on the analytical ETC path. Absolute SNR values are planning estimates, not an observatory-calibrated product.

## Repository contents

| Path | Description |
|------|-------------|
| [`mkid_ifts_sim/`](mkid_ifts_sim/) | Core simulator: sources, atmosphere, sky, telescope, IFTS, MKID, order sorting, recovery, SNR, ETC, full simulation |
| [`web/`](web/) | FastAPI backend and React/Vite frontend — see [`web/README.md`](web/README.md) |
| [`notebooks/`](notebooks/) | Worked examples, strategy comparison, config optimization, SITELLE SN3 benchmark |
| [`docs/`](docs/) | [API reference](docs/api_reference.md), [notebook guide](docs/notebooks.md), [benchmark notes](docs/benchmarks.md) |
| [`scripts/`](scripts/) | Regenerate canonical figures and the pipeline overview diagram |
| [`outputs/canonical_figures/`](outputs/canonical_figures/) | Canonical figures `00`–`03` and captions — see [`outputs/canonical_figures/README.md`](outputs/canonical_figures/README.md) |
| [`project_materials/`](project_materials/) | Project overview and development PDFs |
| [`tests/`](tests/) | Package, pipeline, simulation, and web API tests |
| `ifts_mkid_sim.ipynb` | Original exploratory notebook |

Built-in spectral templates ship under `mkid_ifts_sim/data/templates/`. Optional instrument/sky calibration tables live under `mkid_ifts_sim/data/calibration/` (`calibration_profile="tables"` or per-curve filenames).

## Installation

Python 3.10+ (3.11 recommended for API deployment).

```bash
git clone https://github.com/r-nepton/High-res-IFTS-Lab.git
cd High-res-IFTS-Lab
pip install -e ".[test]"
```

Web and API development:

```bash
pip install -e ".[web,test]"
```

Dependencies: `numpy`, `scipy`, `matplotlib`, `astropy`, `PyYAML`.

## Quick start

### Analytical SNR

```python
from mkid_ifts_sim import InstrumentConfig, snr_from_time

config = InstrumentConfig()
source = {"mode": "point", "spectral_type": "stellar_g2v", "magnitude": 20.0, "band": "r"}
result = snr_from_time(source, config, t_total_s=1800.0)
print(result.snr.max())
```

### Command-line ETC

```bash
mkid-ifts-etc request.yaml
```

Supported modes: `snr_from_time`, `time_from_snr`, `optimize_config`. See [`mkid_ifts_sim/etc.py`](mkid_ifts_sim/etc.py) and the [API reference](docs/api_reference.md).

### Full simulation

```python
from mkid_ifts_sim import InstrumentConfig, run_full_simulation

result = run_full_simulation(
    {"mode": "point", "spectral_type": "stellar_g2v", "magnitude": 20.0, "band": "r"},
    InstrumentConfig(),
)
print(result.stitched_spectrum.wavelength_nm[:5])
```

## Web ETC

- **Run locally:** [`web/README.md`](web/README.md) — `uvicorn` for the API and `npm run dev` for the frontend.
- **Production frontend:** build `web/app` with `VITE_API_URL=https://mkid-ifts-api.onrender.com`, deploy `dist/` to Cloudflare Pages.
- **Production backend:** `Dockerfile.web`, `render.yaml`, and `runtime.txt` (Python 3.11) for Render or similar hosts.

## Notebooks

| Notebook | Topic |
|----------|--------|
| [`worked_example.ipynb`](notebooks/worked_example.ipynb) | End-to-end simulation chain |
| [`strategy_comparison.ipynb`](notebooks/strategy_comparison.ipynb) | Hard-cut vs probabilistic order sorting |
| [`config_optimization.ipynb`](notebooks/config_optimization.ipynb) | SNR vs scan parameters |
| [`sitelle_sn3_benchmark.ipynb`](notebooks/sitelle_sn3_benchmark.ipynb) | SN3-like filtered FTS reference |

## Figures

```bash
python scripts/generate_pipeline_figure.py
python scripts/generate_usable_figures.py
python scripts/generate_strategy_figure.py
```

## Model coverage and next steps

**Covers**

- MKID-IFTS signal chain and order-sorting strategy trades
- Analytical ETC (web) and full folded-order simulation (package)
- Telescope / scan / MKID / observing configuration
- Optional wavelength tables for QE, \(R_E\), mirror, optics, and sky continuum

**Does not cover yet**

- Observatory-calibrated absolute SNR for a specific site
- Full MKID array effects (crosstalk, non-uniformity)
- Full-field imaging cubes
- Site atmosphere/sky without supplied tables

**Next steps**

- Insert measured MKID and optics curves via calibration tables
- Add site atmosphere and sky tables when available
- Extend imaging / multi-pixel modeling
- Benchmark against lab or SITELLE-like reference cases

## Testing

```bash
pytest
```

## Citation and materials

Project context and references are in `project_materials/`. The web Credits tab links to the latest overview PDF served from the API.
