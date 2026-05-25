from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import yaml

from .atmosphere import transmission
from .config import InstrumentConfig
from .ifts import optics_transmission
from .sky_background import sky_spectrum
from .snr import SNRResult, compute_snr
from .source import Spectrum, make_input_source
from .telescope import ThroughputResult, throughput_components


def prepare_observation(source: Spectrum | Mapping[str, Any], config: InstrumentConfig) -> ThroughputResult:
    """Propagate a source through atmosphere, sky, and telescope throughput.

    Parameters
    ----------
    source:
        Either a fully constructed `Spectrum` or a source request mapping accepted
        by `make_input_source()`.
    config:
        Instrument and observing configuration.

    Returns
    -------
    ThroughputResult
        Detector-entering source and sky rates in photons s^-1 nm^-1 on the
        simulator wavelength grid.
    """
    spectrum = source if isinstance(source, Spectrum) else make_input_source(source, config)
    wavelength_nm = config.wavelength_grid_nm()
    source_resampled = spectrum.resample(config.sigma_grid())
    atmospheric = transmission(wavelength_nm, config.airmass, config.altitude_m, config.pwv_mm)
    optics = optics_transmission(wavelength_nm, config)
    source_post_atm = source_resampled.flux_photons_per_s_cm2_nm * atmospheric * optics
    sky = sky_spectrum(
        wavelength_nm,
        moon_phase=config.moon_phase,
        altitude_m=config.altitude_m,
        T_amb=config.ambient_temp_k,
        emissivity=config.thermal_emissivity,
    ) * optics
    return throughput_components(wavelength_nm, config, source_post_atm, sky)


def snr_from_time(source: Spectrum | Mapping[str, Any], config: InstrumentConfig, t_total_s: float) -> SNRResult:
    """Compute the analytical SNR curve for a fixed total observing time."""
    per_step = max(t_total_s / config.n_steps, 1.0e-6)
    working_config = config.with_updates(t_exp_per_step_s=per_step)
    rates = prepare_observation(source, working_config)
    return compute_snr(rates.source_rate_per_nm, rates.sky_rate_per_nm, working_config, working_config.strategy)


def time_from_snr(
    source: Spectrum | Mapping[str, Any],
    config: InstrumentConfig,
    target_snr: float,
    ref_nm: float,
) -> float:
    """Solve for the total observing time needed to reach a target SNR."""
    base_result = snr_from_time(source, config, t_total_s=1.0)
    ref_snr = float(np.interp(ref_nm, base_result.wavelength_nm[::-1], base_result.snr[::-1]))
    if ref_snr <= 0:
        raise ValueError("Reference SNR is zero; requested configuration cannot reach target.")
    return float((target_snr / ref_snr) ** 2)


def optimize_config(source: Spectrum | Mapping[str, Any], science_goal: Mapping[str, Any]) -> InstrumentConfig:
    """Search a small discrete configuration grid for a high-SNR setup."""
    ref_nm = float(science_goal.get("ref_nm", 656.3))
    target_snr = float(science_goal.get("target_snr", 10.0))
    target_resolution = float(science_goal.get("target_resolution", 3000.0))
    max_time_s = float(science_goal.get("max_time_s", 3600.0))

    candidate_steps = [1024, 1536, 2048, 3072]
    candidate_delta_x = [6.0e-6, 3.0e-6, 2.0e-6, 1.0e-6]
    strategies = ["hard_cut", "probabilistic"]

    best_score = -np.inf
    best_config = InstrumentConfig()
    sigma_ref = 1.0e7 / ref_nm

    for n_steps in candidate_steps:
        for delta_x in candidate_delta_x:
            for strategy in strategies:
                config = InstrumentConfig(
                    n_steps=n_steps,
                    delta_x_m=delta_x,
                    strategy=strategy,
                    t_exp_per_step_s=max_time_s / n_steps,
                )
                opd_max = (n_steps - config.zpd_index - 1) * delta_x * 100.0
                resolving_power = 2.0 * opd_max * sigma_ref
                if resolving_power < 0.8 * target_resolution:
                    continue
                result = snr_from_time(source, config, max_time_s)
                snr_at_ref = float(np.interp(ref_nm, result.wavelength_nm[::-1], result.snr[::-1]))
                score = snr_at_ref - 5.0 * float(result.saturation_warning)
                if score > best_score:
                    best_score = score
                    best_config = config
    return best_config


def load_request(path: str | Path) -> dict[str, Any]:
    """Load a JSON or YAML ETC request file."""
    path = Path(path)
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix == ".json":
        return json.loads(text)
    if suffix in {".yml", ".yaml"}:
        return yaml.safe_load(text)
    raise ValueError("ETC request files must be JSON or YAML.")


def _result_to_dict(result: SNRResult) -> dict[str, Any]:
    return {
        "wavelength_nm": result.wavelength_nm[::-1].tolist(),
        "snr": result.snr[::-1].tolist(),
        "source_counts": result.source_counts[::-1].tolist(),
        "saturation_warning": result.saturation_warning,
    }


def main(argv: list[str] | None = None) -> int:
    """Run the command-line ETC entry point."""
    parser = argparse.ArgumentParser(description="MKID-IFTS analytical ETC")
    parser.add_argument("request_file", help="Path to a JSON or YAML request file.")
    args = parser.parse_args(argv)

    payload = load_request(args.request_file)
    config = InstrumentConfig.from_mapping(payload.get("config", {}))
    source_request = payload.get("source", {"mode": "point"})
    mode = payload.get("mode", "snr_from_time")

    if mode == "snr_from_time":
        t_total_s = float(payload.get("t_total_s", config.total_observing_time_s))
        output = _result_to_dict(snr_from_time(source_request, config, t_total_s))
    elif mode == "time_from_snr":
        target_snr = float(payload["target_snr"])
        ref_nm = float(payload["ref_nm"])
        output = {"t_total_s": time_from_snr(source_request, config, target_snr, ref_nm)}
    elif mode == "optimize_config":
        goal = payload["science_goal"]
        best = optimize_config(source_request, goal)
        output = {"config": best.to_dict()}
    else:
        raise ValueError(f"Unsupported ETC mode: {mode}")

    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
