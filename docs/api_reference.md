# API Reference

## Core Configuration

- `mkid_ifts_sim.InstrumentConfig`
  - Central simulator configuration dataclass.
  - Covers telescope, IFTS, MKID, observing, order-sorting, and processing parameters.
  - `calibration_profile`: `"parametric"` (default formulas) or `"tables"` (packaged CSVs under `data/calibration/`).
  - Optional per-curve overrides: `qe_curve`, `re_curve`, `mirror_reflectivity_curve`, `optics_transmission_curve`, `sky_continuum_curve`.

## Source Construction

- `mkid_ifts_sim.load_template(name, **kwargs)`
  - Load a built-in spectral template on the simulator wavenumber grid.
- `mkid_ifts_sim.blackbody(T_eff, mag, band="r")`
  - Build a blackbody spectrum normalized to an AB magnitude.
- `mkid_ifts_sim.emission_lines(lines_dict, fwhm_kms=100.0)`
  - Build a configurable emission-line spectrum.
- `mkid_ifts_sim.from_file(path)`
  - Load a CSV, text, or FITS spectrum and resample it to the simulator grid.

## Analytical Path

- `mkid_ifts_sim.make_input_source(request, config=None)`
  - Build a spectrum from a request dict. Emission-line types (`hii_region`, `planetary_nebula`) use `line_flux` and are not AB-normalized at continuum-free bands.
- `mkid_ifts_sim.prepare_observation(source, config)`
  - Apply atmosphere, modeled sky background, telescope throughput, and IFTS optics throughput.
- `mkid_ifts_sim.compute_snr(source_rate_per_nm, sky_rate_per_nm, config, strategy=None)`
  - Compute analytical SNR per recovered spectral channel.
- `mkid_ifts_sim.snr_from_time(source, config, t_total_s)`
  - Return the analytical SNR curve for a total observing time.
- `mkid_ifts_sim.time_from_snr(source, config, target_snr, ref_nm)`
  - Solve for the exposure time required to hit a target SNR.
- `mkid_ifts_sim.optimize_config(source, science_goal, base_config=None)`
  - Search a discrete scan/strategy grid; telescope and MKID settings are taken from `base_config` when provided.

## Full Simulation Path

- `mkid_ifts_sim.run_full_simulation(source, config, include_noise=True, include_sky=True)`
  - Run the folded-order simulation end to end.
- `mkid_ifts_sim.estimate_full_mode_snr(source, config, n_realizations=12, include_sky=True)`
  - Measure full-mode SNR from repeated noisy realizations.

## Interferogram and Recovery Utilities

- `mkid_ifts_sim.generate_interferogram(spectrum_per_nm, sigma_cm, config)`
- `mkid_ifts_sim.combine_dual_output(I0, I1)`
- `mkid_ifts_sim.recover_order_spectrum(interferogram, delta_x_m, n_zpd, ...)`
- `mkid_ifts_sim.stitch_orders(order_spectra, order_layout, taper_width_bins=10)`

## Detector and Order Sorting Utilities

- `mkid_ifts_sim.energy_resolution(wavelength_nm, config)`
- `mkid_ifts_sim.apply_dead_time(rate_hz, dead_time_us)`
- `mkid_ifts_sim.check_saturation(rate_hz, config)`
- `mkid_ifts_sim.hard_cut_assignment(...)`
- `mkid_ifts_sim.probabilistic_assignment(...)`
- `mkid_ifts_sim.contamination_fraction(R_E, order_width_eV)`
- `mkid_ifts_sim.grey_zone_loss(R_E, order_width_eV, k_sigma)`

## Sky Model Utilities

- `mkid_ifts_sim.sky_spectrum(wavelength_nm, moon_phase, altitude_m, ...)`
- `mkid_ifts_sim.oh_lines(wavelength_nm)`
- `mkid_ifts_sim.thermal_background(wavelength_nm, T_amb, emissivity)`
