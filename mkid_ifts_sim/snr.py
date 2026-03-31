from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import InstrumentConfig
from .ifts import nm_flux_to_sigma_flux
from .mkid_detector import apply_dead_time, check_saturation, qe
from .order_sorting import sort_spectrum_into_orders


@dataclass(slots=True)
class NoiseComponents:
    sigma_cm: np.ndarray
    wavelength_nm: np.ndarray
    source_counts: np.ndarray
    sky_distributed_noise: np.ndarray
    contamination_noise: np.ndarray
    dark_noise: np.ndarray
    total_noise: np.ndarray


@dataclass(slots=True)
class SNRResult:
    sigma_cm: np.ndarray
    wavelength_nm: np.ndarray
    snr: np.ndarray
    source_counts: np.ndarray
    components: NoiseComponents
    saturation_warning: bool


def noise_breakdown(config: InstrumentConfig, source_spec: np.ndarray, sky_spec: np.ndarray) -> NoiseComponents:
    wavelength_nm = config.wavelength_grid_nm()
    sigma_cm = config.sigma_grid()
    qe_curve = qe(wavelength_nm, config.qe_model)

    source_rate = np.asarray(source_spec, dtype=float) * qe_curve
    sky_rate = np.asarray(sky_spec, dtype=float) * qe_curve
    total_rate = source_rate + sky_rate + config.dark_rate_hz
    dead_time_factor = np.divide(
        apply_dead_time(total_rate, config.dead_time_us),
        np.maximum(total_rate, 1.0e-18),
    )
    source_rate *= dead_time_factor
    sky_rate *= dead_time_factor

    source_orders = sort_spectrum_into_orders(sigma_cm, source_rate, config)
    sky_orders = sort_spectrum_into_orders(sigma_cm, sky_rate, config)

    delta_sigma = np.gradient(sigma_cm)
    t_total = config.total_observing_time_s
    source_counts = np.zeros_like(sigma_cm)
    sky_noise = np.zeros_like(sigma_cm)
    contamination_noise = np.zeros_like(sigma_cm)

    for order_idx, (lo, hi) in enumerate(source_orders.layout.order_bounds_cm):
        mask = (sigma_cm >= lo) & (sigma_cm < hi if hi < sigma_cm[-1] else sigma_cm <= hi)
        if not np.any(mask):
            continue
        n_channels = int(np.count_nonzero(mask))
        src_sigma = nm_flux_to_sigma_flux(wavelength_nm[mask], source_orders.order_spectra_per_nm[order_idx, mask])
        sky_sigma = nm_flux_to_sigma_flux(wavelength_nm[mask], sky_orders.order_spectra_per_nm[order_idx, mask])
        source_counts[mask] = src_sigma * delta_sigma[mask] * t_total
        sky_total_order = float(np.sum(sky_sigma * delta_sigma[mask]) * t_total)
        sky_noise[mask] = np.sqrt(max(sky_total_order, 0.0) / max(n_channels, 1))
        contamination_noise[mask] = source_orders.contamination_fraction[mask] * np.maximum(source_counts[mask], 0.0)

    dark_noise = np.sqrt(np.full_like(source_counts, config.dark_rate_hz * t_total))
    total_noise = np.sqrt(np.maximum(source_counts, 0.0) + sky_noise**2 + contamination_noise**2 + dark_noise**2)
    return NoiseComponents(
        sigma_cm=sigma_cm,
        wavelength_nm=wavelength_nm,
        source_counts=source_counts,
        sky_distributed_noise=sky_noise,
        contamination_noise=contamination_noise,
        dark_noise=dark_noise,
        total_noise=total_noise,
    )


def compute_snr(
    source_spec: np.ndarray,
    sky_spec: np.ndarray,
    config: InstrumentConfig,
    strategy: str | None = None,
) -> SNRResult:
    working_config = config.with_updates(strategy=strategy) if strategy is not None else config
    components = noise_breakdown(working_config, source_spec, sky_spec)
    snr = np.divide(
        components.source_counts,
        components.total_noise,
        out=np.zeros_like(components.source_counts),
        where=components.total_noise > 0,
    )
    snr *= np.sqrt(working_config.n_pixels)
    saturation = check_saturation(source_spec + sky_spec, working_config)
    return SNRResult(
        sigma_cm=components.sigma_cm,
        wavelength_nm=components.wavelength_nm,
        snr=snr,
        source_counts=components.source_counts,
        components=components,
        saturation_warning=saturation,
    )
