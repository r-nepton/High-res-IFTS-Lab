from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import InstrumentConfig


HC_EV_NM = 1239.841984


@dataclass(slots=True)
class DetectorRateResult:
    wavelength_nm: np.ndarray
    qe_curve: np.ndarray
    source_rate_per_nm: np.ndarray
    sky_rate_per_nm: np.ndarray
    total_rate_per_nm: np.ndarray
    dead_time_factor: np.ndarray
    saturation_warning: bool


def _parametric_qe(wavelength_nm: np.ndarray, model: str) -> np.ndarray:
    wavelength_nm = np.asarray(wavelength_nm, dtype=float)
    if model == "baseline":
        response = 0.15 + 0.70 * np.exp(-0.5 * ((wavelength_nm - 720.0) / 260.0) ** 2)
    elif model == "blue_optimized":
        response = 0.12 + 0.72 * np.exp(-0.5 * ((wavelength_nm - 560.0) / 220.0) ** 2)
    elif model == "red_optimized":
        response = 0.10 + 0.74 * np.exp(-0.5 * ((wavelength_nm - 860.0) / 260.0) ** 2)
    else:
        raise ValueError("Unknown QE model.")
    return np.clip(response, 0.0, 1.0)


def qe(wavelength_nm: np.ndarray, model: str = "baseline", config: InstrumentConfig | None = None) -> np.ndarray:
    wavelength_nm = np.asarray(wavelength_nm, dtype=float)
    if config is None:
        return _parametric_qe(wavelength_nm, model)
    from .calibration import resolve_curve

    return resolve_curve(
        wavelength_nm,
        config,
        "qe",
        lambda: _parametric_qe(wavelength_nm, config.qe_model),
    )


def _parametric_energy_resolution(wavelength_nm: np.ndarray, config: InstrumentConfig) -> np.ndarray:
    wavelength_nm = np.asarray(wavelength_nm, dtype=float)
    ref = config.R_energy_ref
    if config.R_energy_scaling == "sqrt":
        resolution = ref * np.sqrt(config.R_energy_ref_nm / wavelength_nm)
    elif config.R_energy_scaling == "linear":
        resolution = ref * (config.R_energy_ref_nm / wavelength_nm)
    elif config.R_energy_scaling == "flat":
        resolution = np.full_like(wavelength_nm, ref)
    else:
        raise ValueError("Unknown energy resolution scaling.")
    return np.maximum(resolution, 1.0)


def energy_resolution(wavelength_nm: np.ndarray, config: InstrumentConfig) -> np.ndarray:
    from .calibration import resolve_curve

    wavelength_nm = np.asarray(wavelength_nm, dtype=float)
    return resolve_curve(
        wavelength_nm,
        config,
        "re",
        lambda: _parametric_energy_resolution(wavelength_nm, config),
    )


def energy_sigma_eV(wavelength_nm: np.ndarray, config: InstrumentConfig) -> np.ndarray:
    wavelength_nm = np.asarray(wavelength_nm, dtype=float)
    return (HC_EV_NM / wavelength_nm) / energy_resolution(wavelength_nm, config)


def apply_dead_time(rate_hz: np.ndarray | float, dead_time_us: float) -> np.ndarray:
    rate_hz = np.asarray(rate_hz, dtype=float)
    tau_s = dead_time_us * 1.0e-6
    return rate_hz / (1.0 + rate_hz * tau_s)


def check_saturation(rate_hz: np.ndarray | float, config: InstrumentConfig) -> bool:
    rate_hz = np.asarray(rate_hz, dtype=float)
    return bool(np.any(rate_hz > config.max_count_rate_hz))


def photon_energy_eV(wavelength_nm: np.ndarray) -> np.ndarray:
    wavelength_nm = np.asarray(wavelength_nm, dtype=float)
    return HC_EV_NM / wavelength_nm


def apply_detector_response(
    wavelength_nm: np.ndarray,
    source_rate_per_nm: np.ndarray,
    sky_rate_per_nm: np.ndarray,
    config: InstrumentConfig,
) -> DetectorRateResult:
    wavelength_nm = np.asarray(wavelength_nm, dtype=float)
    source_rate = np.asarray(source_rate_per_nm, dtype=float)
    sky_rate = np.asarray(sky_rate_per_nm, dtype=float)

    qe_curve = qe(wavelength_nm, config.qe_model, config=config)
    source_detected = source_rate * qe_curve
    sky_detected = sky_rate * qe_curve
    total_detected = source_detected + sky_detected + config.dark_rate_hz
    dead_time_factor = np.divide(
        apply_dead_time(total_detected, config.dead_time_us),
        np.maximum(total_detected, 1.0e-18),
        out=np.ones_like(total_detected),
        where=total_detected > 0,
    )
    source_detected *= dead_time_factor
    sky_detected *= dead_time_factor
    total_post_dead = source_detected + sky_detected + config.dark_rate_hz
    return DetectorRateResult(
        wavelength_nm=wavelength_nm,
        qe_curve=qe_curve,
        source_rate_per_nm=source_detected,
        sky_rate_per_nm=sky_detected,
        total_rate_per_nm=total_post_dead,
        dead_time_factor=dead_time_factor,
        saturation_warning=check_saturation(total_post_dead, config),
    )
