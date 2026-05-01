from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import InstrumentConfig
from .ifts import modulation_efficiency, nm_flux_to_sigma_flux
from .mkid_detector import apply_detector_response
from .order_sorting import sort_spectrum_into_orders


@dataclass(slots=True)
class NoiseComponents:
    sigma_cm: np.ndarray
    wavelength_nm: np.ndarray
    source_counts: np.ndarray
    source_distributed_noise: np.ndarray
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
    """Compute the analytical noise budget on the simulator spectral grid."""
    wavelength_nm = config.wavelength_grid_nm()
    sigma_cm = config.sigma_grid()
    me_curve = modulation_efficiency(wavelength_nm, config.beamsplitter_ratio)
    detected = apply_detector_response(wavelength_nm, source_spec, sky_spec, config)
    source_rate = detected.source_rate_per_nm
    sky_rate = detected.sky_rate_per_nm

    source_orders = sort_spectrum_into_orders(sigma_cm, source_rate, config)
    sky_orders = sort_spectrum_into_orders(sigma_cm, sky_rate, config)

    delta_sigma = np.gradient(sigma_cm)
    t_total = config.total_observing_time_s
    source_counts = np.zeros_like(sigma_cm)
    source_noise = np.zeros_like(sigma_cm)
    sky_noise = np.zeros_like(sigma_cm)
    contamination_noise = np.zeros_like(sigma_cm)

    src_sigma_all = nm_flux_to_sigma_flux(wavelength_nm, source_rate)
    sky_sigma_all = nm_flux_to_sigma_flux(wavelength_nm, sky_rate)

    for order_idx, (lo, hi) in enumerate(source_orders.layout.order_bounds_cm):
        mask = (sigma_cm >= lo) & (sigma_cm < hi if hi < sigma_cm[-1] else sigma_cm <= hi)
        if not np.any(mask):
            continue
        src_sigma = nm_flux_to_sigma_flux(wavelength_nm[mask], source_orders.order_spectra_per_nm[order_idx, mask])
        sky_sigma = nm_flux_to_sigma_flux(wavelength_nm[mask], sky_orders.order_spectra_per_nm[order_idx, mask])
        detected_source_counts = src_sigma * delta_sigma[mask] * t_total
        detected_sky_counts = sky_sigma * delta_sigma[mask] * t_total
        source_counts[mask] = detected_source_counts * me_curve[mask]

        src_order_full = nm_flux_to_sigma_flux(wavelength_nm, source_orders.order_spectra_per_nm[order_idx])
        sky_order_full = nm_flux_to_sigma_flux(wavelength_nm, sky_orders.order_spectra_per_nm[order_idx])
        source_total_order = float(np.sum(src_order_full * delta_sigma) * t_total)
        sky_total_order = float(np.sum(sky_order_full * delta_sigma) * t_total)
        source_noise[mask] = np.sqrt(max(source_total_order, 0.0))
        sky_noise[mask] = np.sqrt(max(sky_total_order, 0.0))
        contamination_fraction = np.clip(source_orders.contamination_fraction[mask], 0.0, 1.0)
        contamination_counts = contamination_fraction * (detected_source_counts + detected_sky_counts) * me_curve[mask]
        contamination_noise[mask] = np.sqrt(np.clip(contamination_counts, 0.0, None))

    dark_noise = np.sqrt(np.full_like(source_counts, config.dark_rate_hz * t_total))
    total_noise = np.sqrt(source_noise**2 + sky_noise**2 + contamination_noise**2 + dark_noise**2)
    return NoiseComponents(
        sigma_cm=sigma_cm,
        wavelength_nm=wavelength_nm,
        source_counts=source_counts,
        source_distributed_noise=source_noise,
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
    """Compute analytical SNR per recovered spectral channel."""
    working_config = config.with_updates(strategy=strategy) if strategy is not None else config
    components = noise_breakdown(working_config, source_spec, sky_spec)
    snr = np.divide(
        components.source_counts,
        components.total_noise,
        out=np.zeros_like(components.source_counts),
        where=components.total_noise > 0,
    )
    if working_config.dual_output:
        snr *= np.sqrt(2.0)
    snr *= np.sqrt(working_config.n_pixels)
    saturation = apply_detector_response(
        working_config.wavelength_grid_nm(),
        source_spec,
        sky_spec,
        working_config,
    ).saturation_warning
    return SNRResult(
        sigma_cm=components.sigma_cm,
        wavelength_nm=components.wavelength_nm,
        snr=snr,
        source_counts=components.source_counts,
        components=components,
        saturation_warning=saturation,
    )
