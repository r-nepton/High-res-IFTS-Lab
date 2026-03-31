from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from .snr import SNRResult
from .source import Spectrum


def plot_spectrum(spectrum: Spectrum, ax: plt.Axes | None = None, label: str | None = None) -> plt.Axes:
    ax = plt.gca() if ax is None else ax
    ax.plot(spectrum.wavelength_nm[::-1], spectrum.flux_photons_per_s_cm2_nm[::-1], label=label)
    ax.set_xlabel("Wavelength [nm]")
    ax.set_ylabel("Flux [photons s$^{-1}$ cm$^{-2}$ nm$^{-1}$]")
    if label:
        ax.legend()
    return ax


def plot_interferogram(opd_m: np.ndarray, interferogram: np.ndarray, ax: plt.Axes | None = None) -> plt.Axes:
    ax = plt.gca() if ax is None else ax
    ax.plot(opd_m * 1.0e3, interferogram)
    ax.set_xlabel("OPD [mm]")
    ax.set_ylabel("Signal [photons s$^{-1}$]")
    return ax


def plot_snr(result: SNRResult, ax: plt.Axes | None = None) -> plt.Axes:
    ax = plt.gca() if ax is None else ax
    ax.plot(result.wavelength_nm[::-1], result.snr[::-1], label="SNR")
    ax.set_xlabel("Wavelength [nm]")
    ax.set_ylabel("SNR per resolution element")
    ax.legend()
    return ax
