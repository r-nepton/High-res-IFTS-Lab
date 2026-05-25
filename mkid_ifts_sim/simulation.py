from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np

from .config import InstrumentConfig
from .ifts import OrderLayout, add_photon_noise, generate_interferogram
from .mkid_detector import DetectorRateResult, apply_detector_response
from .order_sorting import OrderSortingResult, sort_spectrum_into_orders
from .snr import compute_snr
from .source import Spectrum, make_input_source
from .spectrum_recovery import RecoveredOrderSpectrum, recover_order_spectrum, stitch_orders
from .telescope import ThroughputResult


@dataclass(slots=True)
class FullSimulationResult:
    config: InstrumentConfig
    source_spectrum: Spectrum
    throughput: ThroughputResult
    detector_rates: DetectorRateResult
    order_layout: OrderLayout
    source_orders: OrderSortingResult
    sky_orders: OrderSortingResult
    total_orders: OrderSortingResult
    order_port_0: np.ndarray
    order_port_1: np.ndarray
    order_interferograms: np.ndarray
    recovered_orders: list[RecoveredOrderSpectrum]
    stitched_spectrum: Spectrum
    saturation_warning: bool


@dataclass(slots=True)
class FullModeSNRComparison:
    sigma_cm: np.ndarray
    wavelength_nm: np.ndarray
    full_snr: np.ndarray
    analytical_snr: np.ndarray
    signal: np.ndarray
    noise: np.ndarray
    relative_error: np.ndarray
    n_realizations: int


def run_full_simulation(
    source: Spectrum | Mapping[str, Any],
    config: InstrumentConfig,
    include_noise: bool = True,
    include_sky: bool = True,
    rng: np.random.Generator | None = None,
) -> FullSimulationResult:
    """Run the end-to-end folded-order simulation pipeline.

    The returned object contains the intermediate detector-rate, order-sorting,
    interferogram, and recovered-spectrum products needed for debugging or
    notebook-based investigations.
    """
    rng = np.random.default_rng(config.random_seed) if rng is None else rng
    source_spectrum = _coerce_source(source, config)
    from .etc import prepare_observation

    throughput = prepare_observation(source_spectrum, config)

    sky_rate = throughput.sky_rate_per_nm if include_sky else np.zeros_like(throughput.sky_rate_per_nm)
    detector_rates = apply_detector_response(
        throughput.wavelength_nm,
        throughput.source_rate_per_nm,
        sky_rate,
        config,
    )

    sigma_cm = config.sigma_grid()
    source_orders = sort_spectrum_into_orders(sigma_cm, detector_rates.source_rate_per_nm, config)
    sky_orders = sort_spectrum_into_orders(sigma_cm, detector_rates.sky_rate_per_nm, config)
    total_orders = sort_spectrum_into_orders(
        sigma_cm,
        detector_rates.source_rate_per_nm + detector_rates.sky_rate_per_nm,
        config,
    )

    order_port_0, order_port_1, order_interferograms, recovered_orders = _simulate_orders(
        total_orders,
        sigma_cm,
        config,
        include_noise=include_noise,
        rng=rng,
    )
    stitched = stitch_orders(recovered_orders, total_orders.layout)
    return FullSimulationResult(
        config=config,
        source_spectrum=source_spectrum,
        throughput=throughput,
        detector_rates=detector_rates,
        order_layout=total_orders.layout,
        source_orders=source_orders,
        sky_orders=sky_orders,
        total_orders=total_orders,
        order_port_0=order_port_0,
        order_port_1=order_port_1,
        order_interferograms=order_interferograms,
        recovered_orders=recovered_orders,
        stitched_spectrum=stitched,
        saturation_warning=detector_rates.saturation_warning,
    )


def estimate_full_mode_snr(
    source: Spectrum | Mapping[str, Any],
    config: InstrumentConfig,
    n_realizations: int = 12,
    include_sky: bool = True,
) -> FullModeSNRComparison:
    """Estimate full-mode SNR from repeated noisy realizations."""
    if n_realizations < 2:
        raise ValueError("n_realizations must be at least 2.")

    sigma_grid = config.sigma_grid()
    zero_source = Spectrum(sigma_grid, np.zeros_like(sigma_grid), {"template": "zero"})
    source_only = run_full_simulation(source, config, include_noise=False, include_sky=False)
    sky_only = run_full_simulation(zero_source, config, include_noise=False, include_sky=include_sky)

    signal_sigma = source_only.stitched_spectrum.sigma_cm
    source_signal = source_only.stitched_spectrum.flux_photons_per_s_cm2_nm
    sky_baseline = np.interp(
        signal_sigma,
        sky_only.stitched_spectrum.sigma_cm,
        sky_only.stitched_spectrum.flux_photons_per_s_cm2_nm,
        left=0.0,
        right=0.0,
    )

    realizations = []
    for realization_idx in range(n_realizations):
        rng = np.random.default_rng(config.random_seed + realization_idx)
        noisy = run_full_simulation(source, config, include_noise=True, include_sky=include_sky, rng=rng)
        recovered = np.interp(
            signal_sigma,
            noisy.stitched_spectrum.sigma_cm,
            noisy.stitched_spectrum.flux_photons_per_s_cm2_nm,
            left=0.0,
            right=0.0,
        )
        realizations.append(recovered - sky_baseline)

    realizations_arr = np.asarray(realizations)
    noise = np.std(realizations_arr, axis=0, ddof=1)
    full_snr = np.divide(source_signal, noise, out=np.zeros_like(source_signal), where=noise > 0)

    from .etc import snr_from_time
    from .etc import prepare_observation

    if include_sky:
        analytical = snr_from_time(source, config, config.total_observing_time_s)
    else:
        observation = prepare_observation(_coerce_source(source, config), config)
        analytical = compute_snr(
            observation.source_rate_per_nm,
            np.zeros_like(observation.sky_rate_per_nm),
            config,
            config.strategy,
        )
    analytical_snr = np.interp(
        signal_sigma,
        analytical.sigma_cm,
        analytical.snr,
        left=0.0,
        right=0.0,
    )
    relative_error = np.divide(
        np.abs(full_snr - analytical_snr),
        np.maximum(analytical_snr, 1.0e-18),
        out=np.zeros_like(full_snr),
        where=analytical_snr > 0,
    )
    return FullModeSNRComparison(
        sigma_cm=signal_sigma,
        wavelength_nm=1.0e7 / signal_sigma,
        full_snr=full_snr,
        analytical_snr=analytical_snr,
        signal=source_signal,
        noise=noise,
        relative_error=relative_error,
        n_realizations=n_realizations,
    )


def _coerce_source(source: Spectrum | Mapping[str, Any], config: InstrumentConfig) -> Spectrum:
    if isinstance(source, Spectrum):
        return source.resample(config.sigma_grid())
    return make_input_source(source, config)


def _simulate_orders(
    sorted_orders: OrderSortingResult,
    sigma_cm: np.ndarray,
    config: InstrumentConfig,
    include_noise: bool,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[RecoveredOrderSpectrum]]:
    n_orders = sorted_orders.layout.n_orders
    order_port_0 = np.zeros((n_orders, config.n_steps))
    order_port_1 = np.zeros((n_orders, config.n_steps))
    order_interferograms = np.zeros((n_orders, config.n_steps))
    recovered_orders: list[RecoveredOrderSpectrum] = []

    dark_rate_per_order = config.dark_rate_hz / max(n_orders, 1)
    for order_idx, order_number in enumerate(sorted_orders.layout.order_numbers):
        order_spectrum = sorted_orders.order_spectra_per_nm[order_idx]
        interferogram = generate_interferogram(order_spectrum, sigma_cm, config, rng=rng)
        port_0 = interferogram.expected_port_0
        port_1 = interferogram.expected_port_1
        if include_noise:
            port_0 = add_photon_noise(port_0, config.t_exp_per_step_s, rng)
            port_1 = add_photon_noise(port_1, config.t_exp_per_step_s, rng)
            if dark_rate_per_order > 0:
                port_0 = port_0 + add_photon_noise(np.full_like(port_0, dark_rate_per_order), config.t_exp_per_step_s, rng)
                port_1 = port_1 + add_photon_noise(np.full_like(port_1, dark_rate_per_order), config.t_exp_per_step_s, rng)

        science_interferogram = 0.5 * (port_0 - port_1) if config.dual_output else port_0
        order_port_0[order_idx] = port_0
        order_port_1[order_idx] = port_1
        order_interferograms[order_idx] = science_interferogram

        recovered = recover_order_spectrum(
            science_interferogram,
            config.delta_x_m,
            config.zpd_index,
            phase_method=config.phase_method,
            apodization_window=config.apodization,
            order_index=order_idx,
            order_number=int(order_number),
            sigma_nyquist_cm=config.sigma_nyquist_cm,
        )
        lo, hi = sorted_orders.layout.order_bounds_cm[order_idx]
        mask = (recovered.sigma_cm >= lo) & (recovered.sigma_cm <= hi)
        recovered_orders.append(
            RecoveredOrderSpectrum(
                sigma_cm=recovered.sigma_cm[mask],
                flux=recovered.flux[mask],
                order_index=order_idx,
            )
        )

    return order_port_0, order_port_1, order_interferograms, recovered_orders
