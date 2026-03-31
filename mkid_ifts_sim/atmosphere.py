from __future__ import annotations

import numpy as np


def transmission(wavelength_nm: np.ndarray, airmass: float, altitude_m: float, pwv_mm: float = 2.5) -> np.ndarray:
    wavelength_nm = np.asarray(wavelength_nm, dtype=float)
    wavelength_um = wavelength_nm / 1000.0
    altitude_scale = np.exp(-altitude_m / 8000.0)

    rayleigh_tau = 0.00864 * altitude_scale * np.maximum(wavelength_um, 0.32) ** (-4.09)
    aerosol_tau = 0.0035 * altitude_scale * np.maximum(wavelength_um, 0.32) ** (-1.1)

    baseline = np.exp(-(rayleigh_tau + aerosol_tau))
    o2_a = 1.0 - 0.35 * np.exp(-0.5 * ((wavelength_nm - 760.5) / 2.8) ** 2)
    h2o_720 = 1.0 - 0.08 * (pwv_mm / 2.5) * np.exp(-0.5 * ((wavelength_nm - 720.0) / 8.5) ** 2)
    h2o_820 = 1.0 - 0.16 * (pwv_mm / 2.5) * np.exp(-0.5 * ((wavelength_nm - 820.0) / 12.0) ** 2)
    h2o_940 = 1.0 - 0.45 * (pwv_mm / 2.5) * np.exp(-0.5 * ((wavelength_nm - 940.0) / 18.0) ** 2)
    ozone = 1.0 - 0.18 * np.exp(-0.5 * ((wavelength_nm - 600.0) / 180.0) ** 2)

    t_zenith = np.clip(baseline * o2_a * h2o_720 * h2o_820 * h2o_940 * ozone, 0.0, 1.0)
    if airmass <= 0:
        return np.ones_like(wavelength_nm)
    return np.clip(t_zenith**airmass, 0.0, 1.0)
