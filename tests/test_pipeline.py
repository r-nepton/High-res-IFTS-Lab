from __future__ import annotations

import numpy as np

from mkid_ifts_sim import (
    InstrumentConfig,
    RecoveredOrderSpectrum,
    apodize,
    fft_to_spectrum,
    optimize_config,
    phase_correction,
    prepare_observation,
    recover_order_spectrum,
    remove_dc,
    snr_from_time,
    stitch_orders,
    time_from_snr,
)
from mkid_ifts_sim.ifts import opd_positions
from mkid_ifts_sim.source import make_input_source


def test_fft_recovery_recovers_known_frequency() -> None:
    n = 1024
    delta_x_m = 1.0e-6
    sigma0 = 1_850.0
    opd_cm = (np.arange(n) - n // 2) * delta_x_m * 100.0
    interferogram = np.cos(2.0 * np.pi * sigma0 * opd_cm)
    recovered_sigma, recovered = fft_to_spectrum(interferogram, delta_x_m)
    peak = recovered_sigma[np.argmax(np.abs(recovered))]
    assert abs(peak - sigma0) < 2.0 * (recovered_sigma[1] - recovered_sigma[0])


def test_dc_removal_phase_and_apodization_are_finite() -> None:
    cfg = InstrumentConfig(n_steps=256, zpd_fraction=0.5)
    opd = opd_positions(cfg)
    interferogram = 10.0 + np.cos(2.0 * np.pi * 50.0 * opd * 100.0)
    processed = apodize(phase_correction(remove_dc(interferogram), cfg.zpd_index, "mertz"), "hanning")
    assert abs(np.mean(remove_dc(interferogram))) < 1.0e-12
    assert np.all(np.isfinite(processed))


def test_order_stitching_returns_clean_broadband_spectrum() -> None:
    order_a = RecoveredOrderSpectrum(np.linspace(10_000.0, 12_000.0, 64), np.ones(64), order_index=0)
    order_b = RecoveredOrderSpectrum(np.linspace(11_800.0, 14_000.0, 64), np.ones(64) * 2.0, order_index=1)
    layout = type(
        "Layout",
        (),
        {"sigma_min_cm": 10_000.0, "sigma_max_cm": 14_000.0},
    )()
    stitched = stitch_orders([order_a, order_b], layout, taper_width_bins=8)
    assert np.all(np.isfinite(stitched.flux_photons_per_s_cm2_nm))
    assert stitched.sigma_cm[0] >= 10_000.0
    assert stitched.sigma_cm[-1] <= 14_000.0


def test_etc_modes_produce_values() -> None:
    cfg = InstrumentConfig()
    source_request = {"mode": "point", "spectral_type": "stellar_g2v", "magnitude": 19.5, "band": "r"}
    snr_result = snr_from_time(source_request, cfg, 1200.0)
    assert np.max(snr_result.snr) > 0.0

    required_time = time_from_snr(source_request, cfg, target_snr=5.0, ref_nm=650.0)
    assert required_time > 0.0

    best = optimize_config(source_request, {"target_snr": 5.0, "ref_nm": 650.0, "target_resolution": 1500.0, "max_time_s": 600.0})
    assert isinstance(best, InstrumentConfig)


def test_prepare_observation_builds_detector_rates() -> None:
    cfg = InstrumentConfig()
    source = make_input_source({"mode": "point", "spectral_type": "stellar_a0v", "magnitude": 20.0}, cfg)
    observation = prepare_observation(source, cfg)
    assert np.all(observation.total_rate_per_nm >= observation.source_rate_per_nm)
