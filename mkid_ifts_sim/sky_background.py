from __future__ import annotations

import numpy as np
from scipy.constants import c, h, k


_MOON_SCALE = {
    "new": 1.0,
    "crescent": 2.5,
    "quarter": 5.0,
    "full": 12.0,
}

_OH_LINES = np.array(
    [
        (650.0, 45.0),
        (686.5, 85.0),
        (694.3, 95.0),
        (731.6, 120.0),
        (734.0, 130.0),
        (771.1, 110.0),
        (791.4, 160.0),
        (834.4, 220.0),
        (846.5, 210.0),
        (882.7, 240.0),
        (895.2, 250.0),
        (930.0, 300.0),
        (1002.0, 350.0),
        (1033.0, 380.0),
        (1075.0, 330.0),
    ],
    dtype=float,
)

_ATOMIC_LINES = np.array(
    [
        (557.7, 160.0),
        (589.0, 120.0),
        (630.0, 140.0),
    ],
    dtype=float,
)


def oh_lines(wavelength_nm: np.ndarray) -> np.ndarray:
    wavelength_nm = np.asarray(wavelength_nm, dtype=float)
    lines = np.zeros_like(wavelength_nm)
    for lam0, amp in _OH_LINES:
        sigma_nm = 0.18 + 0.0002 * lam0
        lines += amp * np.exp(-0.5 * ((wavelength_nm - lam0) / sigma_nm) ** 2)
    return lines


def thermal_background(wavelength_nm: np.ndarray, T_amb: float, emissivity: float) -> np.ndarray:
    wavelength_nm = np.asarray(wavelength_nm, dtype=float)
    wavelength_m = wavelength_nm * 1.0e-9
    exponent = (h * c) / (wavelength_m * k * T_amb)
    planck = (2.0 * h * c**2) / (wavelength_m**5) / np.expm1(exponent)
    photons = planck * wavelength_m / (h * c)
    tail = emissivity * photons / np.max(photons)
    suppression = 1.0 / (1.0 + np.exp(-(wavelength_nm - 950.0) / 18.0))
    return 4.0 * tail * suppression


def sky_spectrum(
    wavelength_nm: np.ndarray,
    moon_phase: str,
    altitude_m: float,
    T_amb: float = 273.0,
    emissivity: float = 0.08,
) -> np.ndarray:
    wavelength_nm = np.asarray(wavelength_nm, dtype=float)
    altitude_factor = np.exp(-(altitude_m - 2500.0) / 7000.0)
    moon_scale = _MOON_SCALE.get(moon_phase.lower(), 1.0)

    continuum = moon_scale * altitude_factor * 1.6 * (wavelength_nm / 550.0) ** (-1.35)
    zodiacal = 0.35 * (wavelength_nm / 700.0) ** (-0.4)
    atomic = np.zeros_like(wavelength_nm)
    for lam0, amp in _ATOMIC_LINES:
        atomic += amp * np.exp(-0.5 * ((wavelength_nm - lam0) / 0.20) ** 2)
    thermal = thermal_background(wavelength_nm, T_amb, emissivity)
    return continuum + zodiacal + atomic + oh_lines(wavelength_nm) + thermal
