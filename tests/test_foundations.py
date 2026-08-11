from __future__ import annotations

import numpy as np

from mkid_ifts_sim import (
    InstrumentConfig,
    Spectrum,
    apply_dead_time,
    apply_redshift,
    blackbody,
    check_saturation,
    combine_dual_output,
    compute_snr,
    energy_resolution,
    generate_interferogram,
    load_template,
    remove_dc,
    transmission,
    oh_lines,
    sky_spectrum,
)
from mkid_ifts_sim.order_sorting import sort_spectrum_into_orders


def test_blackbody_peak_tracks_wien_law() -> None:
    spectrum = blackbody(6000.0, mag=18.0, band="r")
    peak_nm = spectrum.wavelength_nm[np.argmax(spectrum.flux_photons_per_s_cm2_nm)]
    expected_nm = 2.897771955e6 / 6000.0
    assert abs(peak_nm - expected_nm) / expected_nm < 0.08


def test_redshift_conserves_integrated_flux() -> None:
    sigma = np.linspace(5_000.0, 50_000.0, 10_000)
    flux = np.exp(-0.5 * ((1.0e7 / sigma - 600.0) / 40.0) ** 2)
    spectrum = Spectrum(sigma, flux)
    shifted = apply_redshift(spectrum, 0.15)
    assert np.isclose(shifted.integrated_flux(), spectrum.integrated_flux(), rtol=0.02)


def test_atmosphere_airmass_zero_and_o2_band() -> None:
    wavelength_nm = np.linspace(350.0, 1100.0, 2000)
    zero_airmass = transmission(wavelength_nm, airmass=0.0, altitude_m=4200.0)
    nominal = transmission(wavelength_nm, airmass=1.2, altitude_m=4200.0)
    depth_760 = nominal[np.argmin(np.abs(wavelength_nm - 760.0))]
    depth_750 = nominal[np.argmin(np.abs(wavelength_nm - 750.0))]
    assert np.allclose(zero_airmass, 1.0)
    assert depth_760 < depth_750


def test_sky_model_contains_structured_oh_airglow() -> None:
    wavelength_nm = np.linspace(650.0, 1100.0, 4000)
    lines = oh_lines(wavelength_nm)
    sky = sky_spectrum(wavelength_nm, moon_phase="new", altitude_m=4200.0)
    peak_1083 = lines[np.argmin(np.abs(wavelength_nm - 1083.4))]
    local_continuum = np.median(lines[(wavelength_nm > 1060.0) & (wavelength_nm < 1070.0)])
    assert peak_1083 > 20.0 * local_continuum
    assert np.max(sky) > 50.0 * np.median(sky[(wavelength_nm > 650.0) & (wavelength_nm < 700.0)])


def test_interferogram_ports_and_dual_output_behave() -> None:
    cfg = InstrumentConfig(n_steps=512, zpd_fraction=0.5, sigma_min_cm=14_500.0, sigma_max_cm=15_500.0, delta_x_m=1.0e-8)
    sigma = cfg.sigma_grid()
    wavelength_nm = 1.0e7 / sigma
    spec = np.exp(-0.5 * ((wavelength_nm - 656.3) / 0.08) ** 2) * 1.0e5
    result = generate_interferogram(spec, sigma, cfg)
    assert np.std(result.expected_port_0 + result.expected_port_1) < 1.0e-6 * np.mean(result.expected_port_0 + result.expected_port_1)
    combined = combine_dual_output(result.expected_port_0, result.expected_port_1)
    assert abs(np.mean(remove_dc(combined))) < 1.0e-12


def test_detector_scaling_dead_time_and_saturation() -> None:
    cfg = InstrumentConfig(R_energy_ref=40.0, max_count_rate_hz=1000.0)
    wavelength_nm = np.array([350.0, 1100.0])
    resolution = energy_resolution(wavelength_nm, cfg)
    low_rate = apply_dead_time(np.array([1.0, 2.0]), dead_time_us=10.0)
    assert resolution[0] > resolution[1]
    assert np.allclose(low_rate, np.array([1.0, 2.0]), rtol=1.0e-4)
    assert check_saturation(np.array([1200.0]), cfg)


def test_high_resolution_order_sorting_is_clean() -> None:
    cfg = InstrumentConfig(R_energy_ref=1.0e6, delta_x_m=2.0e-6, strategy="probabilistic")
    sigma = cfg.sigma_grid()
    spectrum = np.ones_like(sigma)
    result = sort_spectrum_into_orders(sigma, spectrum, cfg)
    assert np.max(result.contamination_fraction) < 1.0e-6
    assert np.max(result.discarded_fraction) < 1.0e-12


def test_zero_sky_snr_reduces_to_source_only_noise_model() -> None:
    cfg = InstrumentConfig(R_energy_ref=1.0e6, delta_x_m=2.0e-6, dark_rate_hz=0.0)
    source_rate = np.full(cfg.n_sigma, 25.0)
    sky_rate = np.zeros(cfg.n_sigma)
    result = compute_snr(source_rate, sky_rate, cfg)
    valid = result.components.source_distributed_noise > 0
    expected_snr = np.divide(
        result.source_counts[valid],
        result.components.source_distributed_noise[valid],
        out=np.zeros_like(result.source_counts[valid]),
        where=result.components.source_distributed_noise[valid] > 0,
    )
    if cfg.dual_output:
        expected_snr *= np.sqrt(2.0)
    assert np.allclose(result.snr[valid], expected_snr, rtol=1.0e-6)
    assert np.allclose(result.components.sky_distributed_noise, 0.0)
    assert np.allclose(result.components.dark_noise, 0.0)


def test_nonflat_source_noise_is_distributed_across_an_order() -> None:
    cfg = InstrumentConfig(
        R_energy_ref=1.0e6,
        delta_x_m=2.0e-6,
        sigma_min_cm=12_000.0,
        sigma_max_cm=14_000.0,
        dark_rate_hz=0.0,
    )
    sigma = cfg.sigma_grid()
    source_rate = 1.0e-3 + np.exp(-0.5 * ((sigma - 13_000.0) / 5.0) ** 2) * 1.0e4
    result = compute_snr(source_rate, np.zeros_like(source_rate), cfg)

    peak_idx = int(np.argmax(result.source_counts))
    wing_idx = int(np.argmin(np.abs(sigma - 12_500.0)))
    assert result.source_counts[wing_idx] < 1.0e-4 * result.source_counts[peak_idx]
    assert result.components.source_distributed_noise[wing_idx] > 0.95 * result.components.source_distributed_noise[peak_idx]


def test_probabilistic_low_resolution_adds_contamination_noise() -> None:
    cfg = InstrumentConfig(
        R_energy_ref=4.0,
        delta_x_m=2.0e-6,
        strategy="probabilistic",
        dark_rate_hz=0.0,
    )
    source_rate = np.full(cfg.n_sigma, 10.0)
    low_res = compute_snr(source_rate, np.zeros_like(source_rate), cfg)
    high_res = compute_snr(source_rate, np.zeros_like(source_rate), cfg.with_updates(R_energy_ref=1.0e6))

    assert np.max(low_res.components.contamination_noise) > 0.0
    assert np.max(high_res.components.contamination_noise) < 1.0e-8


def test_templates_load_from_package_data() -> None:
    spectrum = load_template("stellar_g2v")
    assert spectrum.flux_photons_per_s_cm2_nm.shape == spectrum.sigma_cm.shape


def test_make_input_source_hii_region_is_not_zeroed() -> None:
    from mkid_ifts_sim import make_input_source

    spectrum = make_input_source(
        {"mode": "point", "spectral_type": "hii_region", "magnitude": 22.0, "band": "r", "line_flux": 0.02}
    )
    assert float(np.max(spectrum.flux_photons_per_s_cm2_nm)) > 0.0


def test_calibration_tables_profile_runs_snr() -> None:
    from mkid_ifts_sim import snr_from_time

    cfg = InstrumentConfig(calibration_profile="tables", n_steps=256, n_sigma=512)
    result = snr_from_time(
        {"mode": "point", "spectral_type": "stellar_g2v", "magnitude": 20.0, "band": "r"},
        cfg,
        t_total_s=256.0,
    )
    assert result.snr.shape == result.wavelength_nm.shape
    assert float(np.max(result.snr)) > 0.0
