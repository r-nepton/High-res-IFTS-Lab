from __future__ import annotations

from dataclasses import dataclass
import math

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
    return float(0.5 * (1.0 - math.erf(order_width_eV / (2.0 * np.sqrt(2.0) * sigma_E))))


def grey_zone_loss(R_E: float, order_width_eV: float, k_sigma: float) -> float:
    sigma_E = order_width_eV / max(R_E, 1.0)
    usable_half_width = max(order_width_eV / 2.0 - k_sigma * sigma_E, 0.0)
    return float(1.0 - (2.0 * usable_half_width / order_width_eV))


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
        discarded = np.zeros_like(sigma_cm)
    elif config.strategy == "hard_cut":
        assignments = hard_cut_assignment(true_energies, sigma_e, boundaries_eV, config.k_sigma)
        valid = assignments >= 0
        in_range = assignments < weights.shape[1]
        weights[np.where(valid & in_range)[0], assignments[valid & in_range]] = 1.0
        discarded = 1.0 - weights.sum(axis=1)
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
