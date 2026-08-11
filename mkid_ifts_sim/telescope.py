from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import InstrumentConfig


@dataclass(slots=True)
class ThroughputResult:
    wavelength_nm: np.ndarray
    source_rate_per_nm: np.ndarray
    sky_rate_per_nm: np.ndarray
    total_rate_per_nm: np.ndarray
    system_throughput: np.ndarray


def collecting_area(D_m: float, obscuration: float) -> float:
    radius_cm = 0.5 * D_m * 100.0
    return float(np.pi * radius_cm**2 * (1.0 - obscuration**2))


def mirror_reflectivity(
    wavelength_nm: np.ndarray,
    coating: str,
    n_refl: int,
    aging_factor: float = 1.0,
    config: InstrumentConfig | None = None,
) -> np.ndarray:
    from .calibration import resolve_curve

    wavelength_nm = np.asarray(wavelength_nm, dtype=float)

    def _parametric_single() -> np.ndarray:
        if coating == "silver":
            anchor_wl = np.array([350.0, 400.0, 500.0, 700.0, 900.0, 1100.0])
            anchor_refl = np.array([0.90, 0.95, 0.97, 0.98, 0.985, 0.98])
        elif coating == "aluminum":
            anchor_wl = np.array([350.0, 400.0, 500.0, 700.0, 900.0, 1100.0])
            anchor_refl = np.array([0.82, 0.88, 0.92, 0.92, 0.915, 0.92])
        else:
            raise ValueError("coating must be 'aluminum' or 'silver'.")
        single_bounce = np.interp(wavelength_nm, anchor_wl, anchor_refl, left=anchor_refl[0], right=anchor_refl[-1])
        return np.clip(single_bounce * aging_factor, 0.0, 1.0)

    if config is None:
        return _parametric_single() ** n_refl

    # Packaged mirror tables are single-bounce reflectivity.
    single = resolve_curve(wavelength_nm, config, "mirror", _parametric_single)
    if config.mirror_reflectivity_curve or config.calibration_profile == "tables":
        single = np.clip(single * aging_factor, 0.0, 1.0)
    return single ** n_refl


def throughput(
    wavelength_nm: np.ndarray,
    config: InstrumentConfig,
    source_flux: np.ndarray,
    sky_flux: np.ndarray,
) -> np.ndarray:
    result = throughput_components(wavelength_nm, config, source_flux, sky_flux)
    return result.total_rate_per_nm


def throughput_components(
    wavelength_nm: np.ndarray,
    config: InstrumentConfig,
    source_flux: np.ndarray,
    sky_flux: np.ndarray,
) -> ThroughputResult:
    wavelength_nm = np.asarray(wavelength_nm, dtype=float)
    source_flux = np.asarray(source_flux, dtype=float)
    sky_flux = np.asarray(sky_flux, dtype=float)
    area_cm2 = collecting_area(config.D_primary, config.obscuration)
    mirror = mirror_reflectivity(
        wavelength_nm,
        config.mirror_coating,
        config.n_reflections,
        config=config,
    )
    nd = config.nd_transmission if config.use_nd_filter else 1.0
    omega_pix = config.pixel_scale_arcsec**2
    system = mirror * nd
    source_rate = source_flux * area_cm2 * system
    sky_rate = sky_flux * omega_pix * area_cm2 * system
    return ThroughputResult(
        wavelength_nm=wavelength_nm,
        source_rate_per_nm=source_rate,
        sky_rate_per_nm=sky_rate,
        total_rate_per_nm=source_rate + sky_rate,
        system_throughput=system,
    )
