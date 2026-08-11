from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import InstrumentConfig


@dataclass(slots=True)
class OrderLayout:
    order_numbers: np.ndarray
    order_edges_cm: np.ndarray
    order_bounds_cm: list[tuple[float, float]]
    sigma_min_cm: float
    sigma_max_cm: float
    free_spectral_range_cm: float

    @property
    def n_orders(self) -> int:
        return len(self.order_bounds_cm)


@dataclass(slots=True)
class InterferogramResult:
    opd_m: np.ndarray
    expected_port_0: np.ndarray
    expected_port_1: np.ndarray
    noisy_port_0: np.ndarray | None = None
    noisy_port_1: np.ndarray | None = None

    @property
    def difference_signal(self) -> np.ndarray:
        return 0.5 * (self.expected_port_0 - self.expected_port_1)


def optics_transmission(wavelength_nm: np.ndarray, config: InstrumentConfig) -> np.ndarray:
    from .calibration import resolve_curve

    wavelength_nm = np.asarray(wavelength_nm, dtype=float)

    def _parametric() -> np.ndarray:
        chromatic = 1.0 - 0.03 * ((wavelength_nm - 700.0) / 450.0) ** 2
        return np.clip(config.optical_transmission * chromatic, 0.0, 1.0)

    return resolve_curve(wavelength_nm, config, "optics", _parametric)


def modulation_efficiency(wavelength_nm: np.ndarray, beamsplitter_ratio: float = 0.5) -> np.ndarray:
    wavelength_nm = np.asarray(wavelength_nm, dtype=float)
    imbalance = np.clip(beamsplitter_ratio + 0.015 * np.sin(2.0 * np.pi * wavelength_nm / 800.0), 0.0, 1.0)
    return 4.0 * imbalance * (1.0 - imbalance)


def opd_positions(config: InstrumentConfig, rng: np.random.Generator | None = None) -> np.ndarray:
    indices = np.arange(config.n_steps)
    opd = (indices - config.zpd_index) * config.delta_x_m
    if config.opd_jitter_rms_m > 0:
        rng = np.random.default_rng(config.random_seed) if rng is None else rng
        opd = opd + rng.normal(scale=config.opd_jitter_rms_m, size=config.n_steps)
    return opd


def modulation_matrix(sigma_cm: np.ndarray, opd_m: np.ndarray, me: np.ndarray) -> np.ndarray:
    sigma_cm = np.asarray(sigma_cm, dtype=float)
    opd_cm = np.asarray(opd_m, dtype=float) * 100.0
    me = np.asarray(me, dtype=float)
    return np.cos(2.0 * np.pi * opd_cm[:, None] * sigma_cm[None, :]) * me[None, :]


def nm_flux_to_sigma_flux(wavelength_nm: np.ndarray, flux_per_nm: np.ndarray) -> np.ndarray:
    wavelength_nm = np.asarray(wavelength_nm, dtype=float)
    flux_per_nm = np.asarray(flux_per_nm, dtype=float)
    return flux_per_nm * (wavelength_nm**2 / 1.0e7)


def fold_sigma_to_local(sigma_cm: np.ndarray, sigma_nyquist_cm: float) -> np.ndarray:
    sigma_cm = np.asarray(sigma_cm, dtype=float)
    order_number = np.floor(sigma_cm / sigma_nyquist_cm).astype(int)
    frac = sigma_cm - order_number * sigma_nyquist_cm
    return np.where(order_number % 2 == 0, frac, sigma_nyquist_cm - frac)


def unfold_local_sigma(local_sigma_cm: np.ndarray, order_number: int, sigma_nyquist_cm: float) -> np.ndarray:
    local_sigma_cm = np.asarray(local_sigma_cm, dtype=float)
    if order_number % 2 == 0:
        return order_number * sigma_nyquist_cm + local_sigma_cm
    return (order_number + 1) * sigma_nyquist_cm - local_sigma_cm


def generate_interferogram(
    spectrum_per_nm: np.ndarray,
    sigma_cm: np.ndarray,
    config: InstrumentConfig,
    rng: np.random.Generator | None = None,
) -> InterferogramResult:
    sigma_cm = np.asarray(sigma_cm, dtype=float)
    wavelength_nm = 1.0e7 / sigma_cm
    opd_m = opd_positions(config, rng=rng)
    me = modulation_efficiency(wavelength_nm, config.beamsplitter_ratio)
    optics = optics_transmission(wavelength_nm, config)
    weighted_spectrum = nm_flux_to_sigma_flux(wavelength_nm, spectrum_per_nm) * optics
    weights = np.gradient(sigma_cm)
    dc = 0.5 * np.sum(weighted_spectrum * weights)
    modulation = modulation_matrix(sigma_cm, opd_m, me)
    ac = 0.5 * (modulation @ (weighted_spectrum * weights))
    port_0 = np.clip(dc + ac, 0.0, None)
    port_1 = np.clip(dc - ac, 0.0, None)
    return InterferogramResult(opd_m=opd_m, expected_port_0=port_0, expected_port_1=port_1)


def add_photon_noise(
    interferogram: np.ndarray,
    t_exp: float,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    rng = np.random.default_rng() if rng is None else rng
    interferogram = np.asarray(interferogram, dtype=float)
    mu = np.clip(interferogram * t_exp, 0.0, None)
    return rng.poisson(mu) / t_exp


def combine_dual_output(I0: np.ndarray, I1: np.ndarray, eps: float = 1.0e-18) -> np.ndarray:
    I0 = np.asarray(I0, dtype=float)
    I1 = np.asarray(I1, dtype=float)
    return (I0 - I1) / np.maximum(I0 + I1, eps)


def folding_orders(config: InstrumentConfig) -> OrderLayout:
    fsr = config.free_spectral_range_cm
    order_min = int(np.floor(config.sigma_min_cm / fsr))
    order_max = int(np.ceil(config.sigma_max_cm / fsr))
    edges = np.arange(order_min, order_max + 1, dtype=float) * fsr
    order_numbers: list[int] = []
    bounds: list[tuple[float, float]] = []
    for order_number, (start, stop) in enumerate(zip(edges[:-1], edges[1:]), start=order_min):
        lo = max(start, config.sigma_min_cm)
        hi = min(stop, config.sigma_max_cm)
        if hi > lo:
            order_numbers.append(order_number)
            bounds.append((lo, hi))
    return OrderLayout(
        order_numbers=np.asarray(order_numbers, dtype=int),
        order_edges_cm=edges,
        order_bounds_cm=bounds,
        sigma_min_cm=config.sigma_min_cm,
        sigma_max_cm=config.sigma_max_cm,
        free_spectral_range_cm=fsr,
    )
