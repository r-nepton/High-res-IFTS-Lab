from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .ifts import OrderLayout, unfold_local_sigma
from .source import Spectrum


@dataclass(slots=True)
class RecoveredOrderSpectrum:
    sigma_cm: np.ndarray
    flux: np.ndarray
    order_index: int


def remove_dc(interferogram: np.ndarray) -> np.ndarray:
    interferogram = np.asarray(interferogram, dtype=float)
    return interferogram - np.mean(interferogram)


def _center_zpd(interferogram: np.ndarray, n_zpd: int) -> np.ndarray:
    center_idx = interferogram.size // 2
    return np.roll(interferogram, center_idx - n_zpd)


def phase_correction(interferogram: np.ndarray, n_zpd: int, method: str = "mertz") -> np.ndarray:
    interferogram = np.asarray(interferogram, dtype=float)
    n_left = n_zpd
    n_right = interferogram.size - n_zpd - 1
    n_overlap = min(n_left, n_right)
    corrected = interferogram.copy()
    if method == "mertz":
        if n_overlap < 1:
            return corrected
        centered = _center_zpd(interferogram, n_zpd)
        short_centered = np.zeros_like(centered)
        center_idx = centered.size // 2
        segment = centered[center_idx - n_overlap : center_idx + n_overlap + 1]
        if segment.size < 3:
            return corrected
        short_centered[center_idx - n_overlap : center_idx + n_overlap + 1] = segment * np.hanning(segment.size)
        full_spectrum = np.fft.rfft(np.fft.ifftshift(centered))
        short_spectrum = np.fft.rfft(np.fft.ifftshift(short_centered))
        phase = np.unwrap(np.angle(short_spectrum))
        corrected_centered = np.fft.fftshift(np.fft.irfft(full_spectrum * np.exp(-1.0j * phase), n=interferogram.size))
        return np.roll(corrected_centered, n_zpd - center_idx)
    elif method == "forman":
        left = interferogram[n_zpd - n_overlap : n_zpd][::-1]
        right = interferogram[n_zpd + 1 : n_zpd + 1 + n_overlap]
        symmetric = 0.5 * (left + right)
        corrected[n_zpd - n_overlap : n_zpd] = symmetric[::-1]
        corrected[n_zpd + 1 : n_zpd + 1 + n_overlap] = 0.75 * right + 0.25 * symmetric
    else:
        raise ValueError("Unknown phase correction method.")
    return corrected


def apodize(interferogram: np.ndarray, window: str = "none") -> np.ndarray:
    interferogram = np.asarray(interferogram, dtype=float)
    n = interferogram.size
    if window == "none":
        win = np.ones(n)
    elif window == "hanning":
        win = np.hanning(n)
    elif window == "gaussian":
        x = np.linspace(-1.0, 1.0, n)
        win = np.exp(-0.5 * (x / 0.35) ** 2)
    elif window == "norton-beer":
        x = np.linspace(-1.0, 1.0, n)
        win = 1.0 - 0.3 * x**2 - 0.7 * x**4
        win = np.clip(win, 0.0, None)
    else:
        raise ValueError("Unknown apodization window.")
    return interferogram * win


def fft_to_spectrum(interferogram: np.ndarray, delta_x: float, zpd_index: int | None = None) -> tuple[np.ndarray, np.ndarray]:
    interferogram = np.asarray(interferogram, dtype=float)
    delta_x_cm = delta_x * 100.0
    centered = _center_zpd(interferogram, zpd_index) if zpd_index is not None else interferogram
    shifted = np.fft.ifftshift(centered)
    spectrum = np.fft.rfft(shifted)
    sigma = np.fft.rfftfreq(interferogram.size, d=delta_x_cm)
    recovered = np.real(spectrum) * 2.0 * delta_x_cm
    return sigma, recovered


def recover_order_spectrum(
    interferogram: np.ndarray,
    delta_x_m: float,
    n_zpd: int,
    phase_method: str = "mertz",
    apodization_window: str = "none",
    order_offset_cm: float = 0.0,
    order_index: int = 0,
    order_number: int | None = None,
    sigma_nyquist_cm: float | None = None,
) -> RecoveredOrderSpectrum:
    corrected = phase_correction(remove_dc(interferogram), n_zpd, phase_method)
    windowed = apodize(corrected, apodization_window)
    sigma_local, flux = fft_to_spectrum(windowed, delta_x_m, zpd_index=n_zpd)
    if order_number is not None and sigma_nyquist_cm is not None:
        sigma_global = unfold_local_sigma(sigma_local, order_number, sigma_nyquist_cm)
    else:
        sigma_global = sigma_local + order_offset_cm
    order = np.argsort(sigma_global)
    return RecoveredOrderSpectrum(sigma_global[order], flux[order], order_index=order_index)


def stitch_orders(
    order_spectra: list[RecoveredOrderSpectrum],
    order_layout: OrderLayout,
    taper_width_bins: int = 10,
) -> Spectrum:
    if not order_spectra:
        raise ValueError("order_spectra cannot be empty.")
    sigma_grid = np.unique(np.concatenate([spec.sigma_cm for spec in order_spectra]))
    total_flux = np.zeros_like(sigma_grid)
    total_weight = np.zeros_like(sigma_grid)

    for spec in order_spectra:
        n = spec.sigma_cm.size
        taper = np.ones(n)
        edge = min(taper_width_bins, max(1, n // 4))
        if edge > 0:
            ramp = np.linspace(0.2, 1.0, edge)
            taper[:edge] *= ramp
            taper[-edge:] *= ramp[::-1]
        flux_interp = np.interp(sigma_grid, spec.sigma_cm, spec.flux, left=0.0, right=0.0)
        weight_interp = np.interp(sigma_grid, spec.sigma_cm, taper, left=0.0, right=0.0)
        total_flux += flux_interp * weight_interp
        total_weight += weight_interp

    stitched_flux = np.divide(total_flux, total_weight, out=np.zeros_like(total_flux), where=total_weight > 0)
    band_mask = (sigma_grid >= order_layout.sigma_min_cm) & (sigma_grid <= order_layout.sigma_max_cm)
    return Spectrum(sigma_grid[band_mask], stitched_flux[band_mask], {"stitched": True})
