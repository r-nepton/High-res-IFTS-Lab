from __future__ import annotations

from typing import Any

import numpy as np
from fastapi import APIRouter, HTTPException

from mkid_ifts_sim import optimize_config, prepare_observation, snr_from_time, time_from_snr
from mkid_ifts_sim import compute_snr

from web.api.instrument import merge_instrument
from web.api.presets import PRESETS
from web.api.serialize import (
    config_summary,
    scalar_stats,
    snr_result_to_dict,
    throughput_to_dict,
)
from web.api.source_build import build_spectrum
from web.api.schemas import (
    CompareStrategiesRequest,
    InstrumentPayload,
    ObservationRatesRequest,
    OptimizeConfigRequest,
    SnrFromTimeRequest,
    SourcePayload,
    TimeFromSnrRequest,
)

router = APIRouter(prefix="/api", tags=["etc"])


def _cfg(source: SourcePayload, inst: InstrumentPayload):
    cfg = merge_instrument(inst)
    spec = build_spectrum(source, cfg)
    return cfg, spec


@router.get("/presets")
def get_presets() -> dict[str, Any]:
    return {"presets": PRESETS}


@router.post("/snr-from-time")
def post_snr_from_time(body: SnrFromTimeRequest) -> dict[str, Any]:
    cfg, spectrum = _cfg(body.source, body.config)
    try:
        result = snr_from_time(spectrum, cfg, body.t_total_s)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    wl = result.wavelength_nm[::-1]
    sn = result.snr[::-1]
    stats = scalar_stats(wl, sn, None)
    return {
        "config_used": config_summary(cfg),
        "t_total_s": body.t_total_s,
        "snr": snr_result_to_dict(result),
        "stats": stats,
    }


@router.post("/time-from-snr")
def post_time_from_snr(body: TimeFromSnrRequest) -> dict[str, Any]:
    cfg, spectrum = _cfg(body.source, body.config)
    try:
        t_total_s = time_from_snr(spectrum, cfg, body.target_snr, body.ref_nm)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"config_used": config_summary(cfg), "t_total_s": t_total_s, "target_snr": body.target_snr, "ref_nm": body.ref_nm}


@router.post("/optimize-config")
def post_optimize_config(body: OptimizeConfigRequest) -> dict[str, Any]:
    _, spectrum = _cfg(body.source, body.config)
    try:
        best = optimize_config(spectrum, body.science_goal.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"config_recommended": config_summary(best), "science_goal": body.science_goal.model_dump()}


@router.post("/observation-rates")
def post_observation_rates(body: ObservationRatesRequest) -> dict[str, Any]:
    cfg, spectrum = _cfg(body.source, body.config)
    try:
        rates = prepare_observation(spectrum, cfg)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"config_used": config_summary(cfg), "rates": throughput_to_dict(rates)}


@router.post("/compare-strategies")
def post_compare_strategies(body: CompareStrategiesRequest) -> dict[str, Any]:
    cfg, spectrum = _cfg(body.source, body.config)
    per_step = max(body.t_total_s / cfg.n_steps, 1.0e-6)
    working = cfg.with_updates(t_exp_per_step_s=per_step)
    try:
        rates = prepare_observation(spectrum, working)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        hard = compute_snr(rates.source_rate_per_nm, rates.sky_rate_per_nm, working, strategy="hard_cut")
        prob = compute_snr(rates.source_rate_per_nm, rates.sky_rate_per_nm, working, strategy="probabilistic")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    wl = hard.wavelength_nm[::-1]
    ratio = np.divide(
        prob.snr[::-1],
        np.maximum(hard.snr[::-1], 1e-30),
        out=np.zeros_like(prob.snr[::-1]),
        where=hard.snr[::-1] > 0,
    )
    return {
        "config_used": config_summary(working),
        "t_total_s": body.t_total_s,
        "hard_cut": snr_result_to_dict(hard, include_noise=False),
        "probabilistic": snr_result_to_dict(prob, include_noise=False),
        "ratio_prob_over_hard": {"wavelength_nm": wl.tolist(), "ratio": ratio.tolist()},
    }
