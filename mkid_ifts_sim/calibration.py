"""Optional wavelength-table calibration curves for matching a real instrument.

Default instrument behavior remains parametric. Set
``InstrumentConfig.calibration_profile = "tables"`` (or set individual curve
names) to interpolate packaged CSVs under ``mkid_ifts_sim/data/calibration/``.
Replace those CSVs with measured lab or site curves using the same columns.
"""

from __future__ import annotations

import csv
from functools import lru_cache
from importlib import resources
from typing import Callable

import numpy as np

from .config import InstrumentConfig

_CURVE_FILES = {
    "qe": "qe_baseline.csv",
    "re": "re_sqrt_ref40.csv",
    "mirror": "mirror_silver.csv",
    "optics": "optics_transmission.csv",
    "sky_continuum": "sky_continuum_dark.csv",
}


@lru_cache(maxsize=16)
def load_calibration_curve(filename: str) -> tuple[np.ndarray, np.ndarray]:
    """Load a two-column calibration CSV: wavelength_nm, value."""
    with resources.as_file(resources.files("mkid_ifts_sim").joinpath("data", "calibration", filename)) as path:
        wavelength_nm: list[float] = []
        values: list[float] = []
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise ValueError(f"Calibration file is empty: {filename}")
            fields = {name.lower(): name for name in reader.fieldnames}
            if "wavelength_nm" not in fields or "value" not in fields:
                raise ValueError(f"Calibration CSV must include wavelength_nm and value columns: {filename}")
            wl_key = fields["wavelength_nm"]
            val_key = fields["value"]
            for row in reader:
                wavelength_nm.append(float(row[wl_key]))
                values.append(float(row[val_key]))
    wl = np.asarray(wavelength_nm, dtype=float)
    vals = np.asarray(values, dtype=float)
    order = np.argsort(wl)
    return wl[order], vals[order]


def interpolate_curve(wavelength_nm: np.ndarray, filename: str) -> np.ndarray:
    wl_tab, val_tab = load_calibration_curve(filename)
    wavelength_nm = np.asarray(wavelength_nm, dtype=float)
    return np.interp(wavelength_nm, wl_tab, val_tab, left=val_tab[0], right=val_tab[-1])


def _curve_name(config: InstrumentConfig, kind: str) -> str | None:
    attr = {
        "qe": "qe_curve",
        "re": "re_curve",
        "mirror": "mirror_reflectivity_curve",
        "optics": "optics_transmission_curve",
        "sky_continuum": "sky_continuum_curve",
    }[kind]
    explicit = getattr(config, attr, None)
    if explicit:
        return str(explicit)
    if config.calibration_profile == "tables":
        return _CURVE_FILES[kind]
    return None


def resolve_curve(
    wavelength_nm: np.ndarray,
    config: InstrumentConfig,
    kind: str,
    parametric: Callable[[], np.ndarray],
) -> np.ndarray:
    """Return a table-interpolated curve when configured, else the parametric result."""
    filename = _curve_name(config, kind)
    if filename is None:
        return parametric()
    return interpolate_curve(wavelength_nm, filename)
