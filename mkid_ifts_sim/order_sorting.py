from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.special import ndtr

from .config import InstrumentConfig
from .ifts import folding_orders, OrderLayout
from .mkid_detector import energy_sigma_eV, photon_energy_eV


E_PER_SIGMA_CM = 1.239841984e-4


@dataclass(slots=True)
class OrderSortingResult:
    order_spectra_per_nm: np.ndarray
    weights: np.ndarray
    contamination_fraction: np.ndarray
    discarded_fraction: np.ndarray
    layout: OrderLayout


def assignment_probabilities(
    E_true: np.ndarray,
    sigma_E: np.ndarray,
    order_boundaries: np.ndarray,
    strategy: str = "probabilistic",
    k_sigma: float = 2.0,
    include_discard: bool = False,
) -> np.ndarray:
    E_true = np.asarray(E_true, dtype=float)
    sigma_E = np.asarray(sigma_E, dtype=float)
    boundaries = np.asarray(order_boundaries, dtype=float)

    if strategy == "probabilistic":
        probabilities = probabilistic_assignment(E_true, sigma_E, boundaries)
    elif strategy == "hard_cut":
        low = boundaries[:-1][None, :] + k_sigma * sigma_E[:, None]
        high = boundaries[1:][None, :] - k_sigma * sigma_E[:, None]
        valid = high > low
        z_low = (low - E_true[:, None]) / sigma_E[:, None]
        z_high = (high - E_true[:, None]) / sigma_E[:, None]
        probabilities = np.where(valid, ndtr(z_high) - ndtr(z_low), 0.0)
    else:
        raise ValueError("Unknown order sorting strategy.")

    probabilities = np.clip(probabilities, 0.0, 1.0)
    if include_discard:
        discarded = np.clip(1.0 - probabilities.sum(axis=1), 0.0, 1.0)
        return np.hstack([probabilities, discarded[:, None]])
    return probabilities


def monte_carlo_assignments(
    E_true: np.ndarray,
    sigma_E: np.ndarray,
    order_boundaries: np.ndarray,
    strategy: str = "probabilistic",
    k_sigma: float = 2.0,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    rng = np.random.default_rng() if rng is None else rng
    probabilities = assignment_probabilities(
        E_true,
        sigma_E,
        order_boundaries,
        strategy=strategy,
        k_sigma=k_sigma,
        include_discard=True,
    )
    cumulative = np.cumsum(probabilities, axis=1)
    cumulative[:, -1] = 1.0
    draws = rng.random(probabilities.shape[0])[:, None]
    assignments = np.argmax(draws <= cumulative, axis=1)
    n_orders = probabilities.shape[1] - 1
    assignments = assignments.astype(int)
    assignments[assignments == n_orders] = -1
    return assignments


def monte_carlo_order_statistics(
    R_E: float,
    order_width_eV: float,
    strategy: str = "probabilistic",
    k_sigma: float = 2.0,
    n_photons: int = 100_000,
    rng: np.random.Generator | None = None,
) -> tuple[float, float]:
    rng = np.random.default_rng() if rng is None else rng
    sigma_E = np.full(n_photons, order_width_eV / max(R_E, 1.0))
    E_true = np.zeros(n_photons)
    boundaries = np.array([-1.5, -0.5, 0.5, 1.5], dtype=float) * order_width_eV
    assignments = monte_carlo_assignments(
        E_true,
        sigma_E,
        boundaries,
        strategy=strategy,
        k_sigma=k_sigma,
        rng=rng,
    )
    contamination = float(np.mean((assignments != 1) & (assignments != -1)))
    discarded = float(np.mean(assignments == -1))
    return contamination, discarded


def hard_cut_assignment(
    E_meas: np.ndarray,
    sigma_E: np.ndarray,
    order_boundaries: np.ndarray,
    k_sigma: float,
) -> np.ndarray:
    E_meas = np.asarray(E_meas, dtype=float)
    sigma_E = np.asarray(sigma_E, dtype=float)
    boundaries = np.asarray(order_boundaries, dtype=float)
    assignments = np.full(E_meas.shape, -1, dtype=int)
    for idx, energy in enumerate(E_meas):
        if np.any(np.abs(energy - boundaries[1:-1]) <= k_sigma * sigma_E[idx]):
            continue
        order = np.searchsorted(boundaries, energy, side="right") - 1
        if 0 <= order < boundaries.size - 1:
            assignments[idx] = order
    return assignments


def probabilistic_assignment(
    E_meas: np.ndarray,
    sigma_E: np.ndarray,
    order_boundaries: np.ndarray,
) -> np.ndarray:
    E_meas = np.asarray(E_meas, dtype=float)
    sigma_E = np.asarray(sigma_E, dtype=float)
    boundaries = np.asarray(order_boundaries, dtype=float)
    z_low = (boundaries[:-1][None, :] - E_meas[:, None]) / sigma_E[:, None]
    z_high = (boundaries[1:][None, :] - E_meas[:, None]) / sigma_E[:, None]
    weights = ndtr(z_high) - ndtr(z_low)
    weights_sum = weights.sum(axis=1, keepdims=True)
    return np.divide(weights, weights_sum, out=np.zeros_like(weights), where=weights_sum > 0)


def contamination_fraction(R_E: float, order_width_eV: float) -> float:
    sigma_E = order_width_eV / max(R_E, 1.0)
    boundaries = np.array([-1.5, -0.5, 0.5, 1.5], dtype=float) * order_width_eV
    probabilities = assignment_probabilities(
        np.array([0.0]),
        np.array([sigma_E]),
        boundaries,
        strategy="probabilistic",
    )
    return float(1.0 - probabilities[0, 1])


def grey_zone_loss(R_E: float, order_width_eV: float, k_sigma: float) -> float:
    sigma_E = order_width_eV / max(R_E, 1.0)
    boundaries = np.array([-1.5, -0.5, 0.5, 1.5], dtype=float) * order_width_eV
    probabilities = assignment_probabilities(
        np.array([0.0]),
        np.array([sigma_E]),
        boundaries,
        strategy="hard_cut",
        k_sigma=k_sigma,
        include_discard=True,
    )
    return float(probabilities[0, -1])


def sort_spectrum_into_orders(
    sigma_cm: np.ndarray,
    spectrum_per_nm: np.ndarray,
    config: InstrumentConfig,
) -> OrderSortingResult:
    sigma_cm = np.asarray(sigma_cm, dtype=float)
    spectrum_per_nm = np.asarray(spectrum_per_nm, dtype=float)
    wavelength_nm = 1.0e7 / sigma_cm
    layout = folding_orders(config)
    boundaries_eV = layout.order_edges_cm * E_PER_SIGMA_CM
    sigma_e = energy_sigma_eV(wavelength_nm, config)
    true_energies = photon_energy_eV(wavelength_nm)

    base_prob = probabilistic_assignment(true_energies, sigma_e, boundaries_eV)
    order_index = np.searchsorted(boundaries_eV, true_energies, side="right") - 1
    order_index = np.clip(order_index, 0, base_prob.shape[1] - 1)

    weights = np.zeros_like(base_prob)
    if config.strategy == "probabilistic":
        weights = base_prob
    elif config.strategy == "hard_cut":
        weights = assignment_probabilities(
            true_energies,
            sigma_e,
            boundaries_eV,
            strategy="hard_cut",
            k_sigma=config.k_sigma,
        )
    else:
        raise ValueError("Unknown order sorting strategy.")

    contamination = 1.0 - weights[np.arange(weights.shape[0]), order_index] - (1.0 - weights.sum(axis=1))
    contamination = np.clip(contamination, 0.0, 1.0)
    order_spectra = weights.T * spectrum_per_nm[None, :]
    return OrderSortingResult(
        order_spectra_per_nm=order_spectra,
        weights=weights,
        contamination_fraction=contamination,
        discarded_fraction=1.0 - weights.sum(axis=1),
        layout=layout,
    )
