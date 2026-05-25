from __future__ import annotations

import numpy as np

from mkid_ifts_sim import (
    InstrumentConfig,
    Spectrum,
    estimate_full_mode_snr,
    fold_sigma_to_local,
    run_full_simulation,
    unfold_local_sigma,
)
from mkid_ifts_sim.order_sorting import contamination_fraction, grey_zone_loss, monte_carlo_order_statistics
from mkid_ifts_sim.source import from_file


def test_fold_unfold_round_trip() -> None:
    cfg = InstrumentConfig(delta_x_m=6.25e-7)
    sigma = np.array([500.0, 7_500.0, 9_000.0, 14_500.0, 23_500.0])
    local = fold_sigma_to_local(sigma, cfg.sigma_nyquist_cm)
    order_number = np.floor(sigma / cfg.sigma_nyquist_cm).astype(int)
    unfolded = np.array(
        [unfold_local_sigma(np.array([loc]), int(order), cfg.sigma_nyquist_cm)[0] for loc, order in zip(local, order_number)]
    )
    assert np.allclose(unfolded, sigma)


def test_full_simulation_recovers_folded_line_peak() -> None:
    cfg = InstrumentConfig(
        n_steps=256,
        n_sigma=1024,
        delta_x_m=6.25e-7,
        sigma_min_cm=12_000.0,
        sigma_max_cm=15_500.0,
        zpd_fraction=0.5,
        airmass=0.0,
        apodization="none",
    )
    sigma = cfg.sigma_grid()
    flux = np.exp(-0.5 * ((sigma - 14_500.0) / 20.0) ** 2) * 1.0e6
    source = Spectrum(sigma, flux)
    result = run_full_simulation(source, cfg, include_noise=False, include_sky=False)
    peak_sigma = result.stitched_spectrum.sigma_cm[np.argmax(result.stitched_spectrum.flux_photons_per_s_cm2_nm)]
    assert abs(peak_sigma - 14_500.0) < 100.0


def test_monte_carlo_order_statistics_match_analytic_helpers() -> None:
    contamination_mc, _ = monte_carlo_order_statistics(
        3.0,
        0.1,
        strategy="probabilistic",
        n_photons=50_000,
        rng=np.random.default_rng(1),
    )
    _, loss_mc = monte_carlo_order_statistics(
        5.0,
        0.1,
        strategy="hard_cut",
        k_sigma=1.0,
        n_photons=50_000,
        rng=np.random.default_rng(2),
    )
    assert abs(contamination_mc - contamination_fraction(3.0, 0.1)) < 0.02
    assert abs(loss_mc - grey_zone_loss(5.0, 0.1, 1.0)) < 0.02


def test_text_spectrum_loader_supports_two_line_format(tmp_path) -> None:
    spectrum_file = tmp_path / "sample_spectrum.txt"
    spectrum_file.write_text(
        "1 2 3 4 5 6 7 8 9 10 11 12\n"
        "350 400 450 500 550 600 650 700 750 800 850 900\n",
        encoding="utf-8",
    )
    spectrum = from_file(spectrum_file)
    assert spectrum.sigma_cm.size == spectrum.flux_photons_per_s_cm2_nm.size
    assert np.max(spectrum.flux_photons_per_s_cm2_nm) > 0


def test_full_mode_comparison_returns_finite_arrays() -> None:
    cfg = InstrumentConfig(
        n_steps=64,
        n_sigma=128,
        delta_x_m=2.0e-6,
        t_exp_per_step_s=0.1,
        apodization="none",
    )
    comparison = estimate_full_mode_snr(
        {"mode": "point", "spectral_type": "stellar_g2v", "magnitude": 17.5, "band": "r"},
        cfg,
        n_realizations=6,
        include_sky=False,
    )
    valid = (comparison.full_snr > 0.5) & (comparison.analytical_snr > 0.5)
    assert comparison.full_snr.shape == comparison.analytical_snr.shape
    assert np.any(np.isfinite(comparison.full_snr))
    assert np.any(comparison.analytical_snr > 0)
    assert np.count_nonzero(valid) > 100
    assert np.median(comparison.relative_error[valid]) < 0.75
