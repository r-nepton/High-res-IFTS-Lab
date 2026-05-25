from __future__ import annotations

import csv
from functools import lru_cache
from importlib import resources

import numpy as np
from scipy.constants import c, h, k

from .source import ab_magnitude_to_photon_flux


_MOON_SCALE = {
    "new": 0.0,
    "crescent": 0.4,
    "quarter": 1.0,
    "full": 2.5,
}

_DARK_SKY_ANCHOR_WAVELENGTH_NM = np.array(
    [350.0, 450.0, 550.0, 650.0, 750.0, 850.0, 950.0, 1050.0],
    dtype=float,
)
_DARK_SKY_ANCHOR_MAG_ARCSEC2 = np.array(
    [22.7, 22.5, 22.1, 21.7, 21.1, 20.0, 18.9, 18.2],
    dtype=float,
)
_OH_INTENSITY_SCALE = 2.0e-5

_ATOMIC_LINES = np.array(
    [
        (557.7, 2.2e-3),
        (589.0, 1.1e-3),
        (630.0, 1.5e-3),
    ],
    dtype=float,
)


@lru_cache(maxsize=1)
def _load_oh_catalog() -> tuple[np.ndarray, np.ndarray]:
    with resources.as_file(resources.files("mkid_ifts_sim").joinpath("data", "sky", "oh_lines.csv")) as path:
        wavelength_nm: list[float] = []
        intensity: list[float] = []
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                wavelength_nm.append(float(row["wavelength_nm"]))
                intensity.append(float(row["relative_intensity"]))
    return np.asarray(wavelength_nm, dtype=float), np.asarray(intensity, dtype=float)


def _dark_sky_continuum(wavelength_nm: np.ndarray) -> np.ndarray:
    sky_mag = np.interp(
        wavelength_nm,
        _DARK_SKY_ANCHOR_WAVELENGTH_NM,
        _DARK_SKY_ANCHOR_MAG_ARCSEC2,
        left=_DARK_SKY_ANCHOR_MAG_ARCSEC2[0],
        right=_DARK_SKY_ANCHOR_MAG_ARCSEC2[-1],
    )
    return np.asarray([ab_magnitude_to_photon_flux(float(wl), float(mag)) for wl, mag in zip(wavelength_nm, sky_mag)], dtype=float)


def oh_lines(wavelength_nm: np.ndarray) -> np.ndarray:
    """Return the OH airglow contribution in photons s^-1 cm^-2 nm^-1 arcsec^-2."""
    wavelength_nm = np.asarray(wavelength_nm, dtype=float)
    line_wavelength_nm, relative_intensity = _load_oh_catalog()
    lines = np.zeros_like(wavelength_nm)
    for lam0, amp in zip(line_wavelength_nm, relative_intensity):
        sigma_nm = 0.10 + 0.00005 * lam0
        lines += (_OH_INTENSITY_SCALE * amp) * np.exp(-0.5 * ((wavelength_nm - lam0) / sigma_nm) ** 2)
    return lines


def thermal_background(wavelength_nm: np.ndarray, T_amb: float, emissivity: float) -> np.ndarray:
    """Approximate the long-wavelength thermal sky tail."""
    wavelength_nm = np.asarray(wavelength_nm, dtype=float)
    wavelength_m = wavelength_nm * 1.0e-9
    exponent = (h * c) / (wavelength_m * k * T_amb)
    planck = (2.0 * h * c**2) / (wavelength_m**5) / np.expm1(exponent)
    photons = planck * wavelength_m / (h * c) * 1.0e-9
    idx_ref = int(np.argmin(np.abs(wavelength_nm - 1100.0)))
    reference = float(photons[idx_ref])
    tail = emissivity * 2.0e-5 * photons / max(reference, 1.0e-30)
    suppression = 1.0 / (1.0 + np.exp(-(wavelength_nm - 950.0) / 18.0))
    return tail * suppression


def sky_spectrum(
    wavelength_nm: np.ndarray,
    moon_phase: str,
    altitude_m: float,
    T_amb: float = 273.0,
    emissivity: float = 0.08,
) -> np.ndarray:
    """Build the total sky spectrum on the requested wavelength grid.

    The continuum is anchored to a dark-sky surface-brightness curve, with a
    moonlight term layered on top and OH/atomic/thermal components added
    separately.
    """
    wavelength_nm = np.asarray(wavelength_nm, dtype=float)
    altitude_factor = np.exp(-(altitude_m - 4200.0) / 9000.0)
    moon_scale = _MOON_SCALE.get(moon_phase.lower(), 0.0)

    dark_continuum = _dark_sky_continuum(wavelength_nm)
    moonlight = moon_scale * ab_magnitude_to_photon_flux(550.0, 21.0) * (wavelength_nm / 550.0) ** (-1.1)
    zodiacal = 0.35 * dark_continuum * (wavelength_nm / 700.0) ** (-0.3)
    atomic = np.zeros_like(wavelength_nm)
    for lam0, amp in _ATOMIC_LINES:
        atomic += amp * np.exp(-0.5 * ((wavelength_nm - lam0) / 0.18) ** 2)
    thermal = thermal_background(wavelength_nm, T_amb, emissivity)
    return altitude_factor * (dark_continuum + moonlight + zodiacal) + atomic + oh_lines(wavelength_nm) + thermal
