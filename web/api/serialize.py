from __future__ import annotations

from typing import Any

import numpy as np

from mkid_ifts_sim import SNRResult
from mkid_ifts_sim import InstrumentConfig
from mkid_ifts_sim.telescope import ThroughputResult


def snr_result_to_dict(result: SNRResult, include_noise: bool = True) -> dict[str, Any]:
    wl = result.wavelength_nm[::-1]
    out: dict[str, Any] = {
        "wavelength_nm": wl.tolist(),
        "snr": result.snr[::-1].tolist(),
        "source_counts": result.source_counts[::-1].tolist(),
        "saturation_warning": result.saturation_warning,
    }
    if include_noise:
        c = result.components
        out["noise"] = {
            "source_distributed": c.source_distributed_noise[::-1].tolist(),
            "sky_distributed": c.sky_distributed_noise[::-1].tolist(),
            "contamination": c.contamination_noise[::-1].tolist(),
            "dark": c.dark_noise[::-1].tolist(),
            "total": c.total_noise[::-1].tolist(),
        }
    return out


def throughput_to_dict(result: ThroughputResult) -> dict[str, Any]:
    wl = result.wavelength_nm[::-1]
    return {
        "wavelength_nm": wl.tolist(),
        "source_rate_per_nm": result.source_rate_per_nm[::-1].tolist(),
        "sky_rate_per_nm": result.sky_rate_per_nm[::-1].tolist(),
        "total_rate_per_nm": result.total_rate_per_nm[::-1].tolist(),
        "system_throughput": result.system_throughput[::-1].tolist(),
    }


def config_summary(cfg: InstrumentConfig) -> dict[str, Any]:
    return {
        **cfg.to_dict(),
        "total_observing_time_s": cfg.total_observing_time_s,
        "sigma_nyquist_cm": cfg.sigma_nyquist_cm,
        "free_spectral_range_cm": cfg.free_spectral_range_cm,
    }


def scalar_stats(wavelength_nm: np.ndarray, snr: np.ndarray, ref_nm: float | None) -> dict[str, Any]:
    wl = np.asarray(wavelength_nm, dtype=float)
    sn = np.asarray(snr, dtype=float)
    peak_idx = int(np.nanargmax(sn))
    out: dict[str, Any] = {
        "snr_max": float(np.nanmax(sn)),
        "snr_max_wavelength_nm": float(wl[peak_idx]),
    }
    if ref_nm is not None:
        out["snr_at_ref_nm"] = float(np.interp(ref_nm, wl, sn))
        out["ref_nm"] = ref_nm
    return out
