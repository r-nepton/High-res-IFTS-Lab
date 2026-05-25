from __future__ import annotations

import numpy as np

from mkid_ifts_sim import (
    InstrumentConfig,
    RecoveredOrderSpectrum,
    Spectrum,
    apodize,
    fft_to_spectrum,
    generate_interferogram,
    optimize_config,
    phase_correction,
    prepare_observation,
    recover_order_spectrum,
    remove_dc,
    run_full_simulation,
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


def test_single_sided_mertz_recovers_line_location() -> None:
    cfg_single = InstrumentConfig(
        n_steps=256,
        n_sigma=1024,
        zpd_fraction=0.10,
        delta_x_m=1.0e-8,
        sigma_min_cm=14_500.0,
        sigma_max_cm=15_500.0,
        apodization="none",
    )
    cfg_centered = cfg_single.with_updates(zpd_fraction=0.50)
    sigma = cfg_single.sigma_grid()
    spectrum = np.exp(-0.5 * ((sigma - 15_000.0) / 2.0) ** 2) * 1.0e5

    single = generate_interferogram(spectrum, sigma, cfg_single)
    centered = generate_interferogram(spectrum, sigma, cfg_centered)
    recovered_single = recover_order_spectrum(
        0.5 * (single.expected_port_0 - single.expected_port_1),
        cfg_single.delta_x_m,
        cfg_single.zpd_index,
        phase_method="mertz",
        apodization_window="none",
    )
    recovered_centered = recover_order_spectrum(
        0.5 * (centered.expected_port_0 - centered.expected_port_1),
        cfg_centered.delta_x_m,
        cfg_centered.zpd_index,
        phase_method="mertz",
        apodization_window="none",
    )

    peak_single = recovered_single.sigma_cm[np.argmax(recovered_single.flux)]
    peak_centered = recovered_centered.sigma_cm[np.argmax(recovered_centered.flux)]
    resolution_bin = recovered_single.sigma_cm[1] - recovered_single.sigma_cm[0]
    amplitude_ratio = np.max(recovered_single.flux) / np.max(recovered_centered.flux)
    assert abs(peak_single - 15_000.0) < 3.0 * resolution_bin
    assert abs(peak_centered - 15_000.0) < 3.0 * resolution_bin
    assert 0.5 < amplitude_ratio < 1.5


def test_full_pipeline_monochromatic_line_is_sinc_like() -> None:
    cfg = InstrumentConfig(
        n_steps=256,
        n_sigma=2048,
        delta_x_m=6.25e-7,
        zpd_fraction=0.5,
        sigma_min_cm=14_000.0,
        sigma_max_cm=15_000.0,
        R_energy_ref=1.0e6,
        apodization="none",
        airmass=0.0,
    )
    sigma = cfg.sigma_grid()
    source = Spectrum(sigma, np.exp(-0.5 * ((sigma - 14_500.0) / 1.0) ** 2) * 1.0e6)
    result = run_full_simulation(source, cfg, include_noise=False, include_sky=False)
    recovered = result.stitched_spectrum
    peak_idx = int(np.argmax(recovered.flux_photons_per_s_cm2_nm))
    peak_sigma = recovered.sigma_cm[peak_idx]
    assert abs(peak_sigma - 14_500.0) < 25.0

    local_mask = np.abs(recovered.sigma_cm - peak_sigma) < 250.0
    local_sigma = recovered.sigma_cm[local_mask] - peak_sigma
    local_flux = recovered.flux_photons_per_s_cm2_nm[local_mask] / recovered.flux_photons_per_s_cm2_nm[peak_idx]
    opd_max_cm = (cfg.n_steps - cfg.zpd_index - 1) * cfg.delta_x_cm
    expected = np.sinc(2.0 * opd_max_cm * local_sigma)
    correlation = np.corrcoef(local_flux, expected)[0, 1]
    assert correlation > 0.8
    assert np.min(local_flux) < 0.0
