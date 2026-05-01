from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from mkid_ifts_sim import InstrumentConfig, load_template, run_full_simulation, snr_from_time
from mkid_ifts_sim.etc import prepare_observation


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs" / "thesis_figures"


def _save(fig: plt.Figure, filename: str) -> None:
    fig.savefig(OUTPUT_DIR / filename, dpi=220, bbox_inches="tight")
    plt.close(fig)


def _style_axes(ax: plt.Axes, title: str, xlabel: str, ylabel: str) -> None:
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.25)


def make_input_conditions() -> None:
    config = InstrumentConfig(
        n_steps=512,
        n_sigma=2048,
        delta_x_m=2.0e-6,
        t_exp_per_step_s=2.0,
        strategy="probabilistic",
        moon_phase="new",
        apodization="none",
    )
    source = load_template("hii_region", sigma_grid_cm=config.sigma_grid(), line_flux=2.0e-2)
    observation = prepare_observation(source, config)

    wavelength_nm = source.wavelength_nm[::-1]
    intrinsic = source.flux_photons_per_s_cm2_nm[::-1]
    detector_wavelength_nm = observation.wavelength_nm[::-1]
    source_rate = observation.source_rate_per_nm[::-1]
    sky_rate = observation.sky_rate_per_nm[::-1]
    total_rate = observation.total_rate_per_nm[::-1]

    fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=False, constrained_layout=True)
    axes[0].plot(wavelength_nm, intrinsic, color="tab:blue", linewidth=1.4)
    _style_axes(
        axes[0],
        "Input Source Spectrum (HII Region Template)",
        "Wavelength [nm]",
        "Flux [photons s$^{-1}$ cm$^{-2}$ nm$^{-1}$]",
    )

    axes[1].plot(detector_wavelength_nm, source_rate, label="Source at detector", linewidth=1.4)
    axes[1].plot(detector_wavelength_nm, sky_rate, label="Sky background", linewidth=1.2)
    axes[1].plot(detector_wavelength_nm, total_rate, label="Total rate", linewidth=1.0, color="black", alpha=0.75)
    axes[1].set_yscale("log")
    _style_axes(
        axes[1],
        "Detector-Entering Photon Rates After Atmosphere + Optics",
        "Wavelength [nm]",
        "Rate [photons s$^{-1}$ nm$^{-1}$]",
    )
    axes[1].legend()
    _save(fig, "01_input_conditions_hii.png")


def make_end_to_end_output() -> None:
    config = InstrumentConfig(
        n_steps=512,
        n_sigma=2048,
        delta_x_m=2.0e-6,
        t_exp_per_step_s=2.0,
        strategy="probabilistic",
        moon_phase="new",
        apodization="none",
    )
    source = load_template("hii_region", sigma_grid_cm=config.sigma_grid(), line_flux=2.0e-2)
    full_result = run_full_simulation(source, config, include_noise=True, include_sky=True)
    analytical = snr_from_time(source, config, config.total_observing_time_s)

    recovered = full_result.stitched_spectrum
    truth = source.resample(recovered.sigma_cm)

    recovered_wavelength_nm = recovered.wavelength_nm[::-1]
    truth_flux = truth.flux_photons_per_s_cm2_nm[::-1]
    recovered_flux = recovered.flux_photons_per_s_cm2_nm[::-1]

    truth_norm = truth_flux / max(np.max(truth_flux), 1.0e-30)
    recovered_norm = recovered_flux / max(np.max(recovered_flux), 1.0e-30)
    snr_curve = analytical.snr[::-1]

    fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True, constrained_layout=True)
    axes[0].plot(recovered_wavelength_nm, truth_norm, label="Input truth (normalized)", linewidth=1.5)
    axes[0].plot(recovered_wavelength_nm, recovered_norm, label="Recovered full simulation (normalized)", linewidth=1.2)
    _style_axes(axes[0], "Recovered Broadband Spectrum vs Input Truth", "", "Normalized flux")
    axes[0].legend()

    axes[1].plot(analytical.wavelength_nm[::-1], snr_curve, color="tab:green", linewidth=1.4)
    _style_axes(axes[1], "Analytical SNR Across the Recovered Band", "Wavelength [nm]", "SNR")
    _save(fig, "02_output_recovery_hii.png")


def make_strategy_comparison() -> list[dict[str, float | str]]:
    base_config = InstrumentConfig(
        n_steps=512,
        n_sigma=2048,
        delta_x_m=2.0e-6,
        t_exp_per_step_s=2.0,
        moon_phase="new",
        apodization="none",
        k_sigma=2.0,
    )
    energy_resolutions = [20.0, 35.0, 50.0, 80.0]
    sources = {
        "HII region": load_template("hii_region", sigma_grid_cm=base_config.sigma_grid(), line_flux=2.0e-2),
        "Faint galaxy": load_template("composite_galaxy", sigma_grid_cm=base_config.sigma_grid(), magnitude=22.0, band="r"),
        "Planetary nebula": load_template("planetary_nebula", sigma_grid_cm=base_config.sigma_grid()),
    }
    ref_nm = {"HII region": 656.3, "Faint galaxy": 750.0, "Planetary nebula": 500.7}

    fig, axes = plt.subplots(1, 3, figsize=(17, 4.6), sharey=True, constrained_layout=True)
    recommendations: list[dict[str, float | str]] = []

    for ax, (name, source) in zip(axes, sources.items()):
        best_entry: tuple[float, str, float] | None = None
        for r_energy in energy_resolutions:
            hard_cfg = base_config.with_updates(R_energy_ref=r_energy, strategy="hard_cut")
            prob_cfg = base_config.with_updates(R_energy_ref=r_energy, strategy="probabilistic")
            hard = snr_from_time(source, hard_cfg, hard_cfg.total_observing_time_s)
            prob = snr_from_time(source, prob_cfg, prob_cfg.total_observing_time_s)
            wavelength_nm = prob.wavelength_nm[::-1]
            ratio = np.divide(prob.snr[::-1], hard.snr[::-1], out=np.ones_like(prob.snr[::-1]), where=hard.snr[::-1] > 0)
            ax.plot(wavelength_nm, ratio, linewidth=1.2, label=f"R_E={r_energy:.0f}")

            hard_ref = float(np.interp(ref_nm[name], hard.wavelength_nm[::-1], hard.snr[::-1]))
            prob_ref = float(np.interp(ref_nm[name], prob.wavelength_nm[::-1], prob.snr[::-1]))
            if best_entry is None or max(hard_ref, prob_ref) > best_entry[0]:
                best_strategy = "probabilistic" if prob_ref >= hard_ref else "hard_cut"
                best_entry = (max(hard_ref, prob_ref), best_strategy, r_energy)

        ax.axhline(1.0, color="black", linestyle="--", linewidth=1.0)
        _style_axes(ax, name, "Wavelength [nm]", "SNR(probabilistic) / SNR(hard-cut)")
        ax.legend(fontsize=8)
        recommendations.append(
            {
                "science_case": name,
                "reference_wavelength_nm": ref_nm[name],
                "preferred_strategy": best_entry[1],
                "preferred_R_energy": best_entry[2],
            }
        )

    _save(fig, "03_strategy_comparison_legacy.png")
    return recommendations


def make_config_optimization(recommendations: list[dict[str, float | str]]) -> list[dict[str, float | str]]:
    candidate_steps = [256, 512, 1024, 2048]
    candidate_delta_x = [6.0e-6, 3.0e-6, 2.0e-6, 1.0e-6]
    case_specs = {
        "HII region": {
            "source": load_template("hii_region", line_flux=2.0e-2),
            "ref_nm": 656.3,
            "t_total_s": 1800.0,
        },
        "Faint galaxy": {
            "source": load_template("composite_galaxy", magnitude=22.0, band="r"),
            "ref_nm": 750.0,
            "t_total_s": 3600.0,
        },
        "Planetary nebula": {
            "source": load_template("planetary_nebula"),
            "ref_nm": 500.7,
            "t_total_s": 1800.0,
        },
    }
    rec_by_name = {row["science_case"]: row for row in recommendations}
    figure, axes = plt.subplots(1, 3, figsize=(16.5, 4.8), constrained_layout=True)
    completed: list[dict[str, float | str]] = []

    for ax, (name, spec) in zip(axes, case_specs.items()):
        strategy = str(rec_by_name[name]["preferred_strategy"])
        r_energy = float(rec_by_name[name]["preferred_R_energy"])
        snr_map = np.zeros((len(candidate_steps), len(candidate_delta_x)))

        for i, n_steps in enumerate(candidate_steps):
            for j, delta_x in enumerate(candidate_delta_x):
                cfg = InstrumentConfig(
                    n_steps=n_steps,
                    n_sigma=2048,
                    delta_x_m=delta_x,
                    t_exp_per_step_s=float(spec["t_total_s"]) / n_steps,
                    strategy=strategy,
                    R_energy_ref=r_energy,
                    moon_phase="new",
                    apodization="none",
                )
                result = snr_from_time(spec["source"], cfg, float(spec["t_total_s"]))
                snr_map[i, j] = float(np.interp(float(spec["ref_nm"]), result.wavelength_nm[::-1], result.snr[::-1]))

        image = ax.imshow(snr_map, origin="lower", aspect="auto", cmap="magma")
        ax.set_xticks(range(len(candidate_delta_x)), [f"{value:.1e}" for value in candidate_delta_x], rotation=40)
        ax.set_yticks(range(len(candidate_steps)), [str(value) for value in candidate_steps])
        _style_axes(ax, name, "delta_x_m", "n_steps")
        best_idx = np.unravel_index(np.argmax(snr_map), snr_map.shape)
        ax.scatter(best_idx[1], best_idx[0], marker="*", s=180, color="cyan", edgecolors="black")
        for (row, col), value in np.ndenumerate(snr_map):
            ax.text(col, row, f"{value:.1f}", ha="center", va="center", color="white", fontsize=8)
        figure.colorbar(image, ax=ax, label="SNR at reference wavelength")

        completed.append(
            {
                "science_case": name,
                "reference_wavelength_nm": float(spec["ref_nm"]),
                "preferred_strategy": strategy,
                "preferred_R_energy": r_energy,
                "best_n_steps": candidate_steps[best_idx[0]],
                "best_delta_x_m": candidate_delta_x[best_idx[1]],
                "best_reference_snr": float(snr_map[best_idx]),
            }
        )

    _save(figure, "04_config_optimization.png")
    return completed


def make_sitelle_benchmark() -> None:
    config = InstrumentConfig(
        sigma_min_cm=1.0e7 / 685.0,
        sigma_max_cm=1.0e7 / 648.0,
        n_sigma=1024,
        delta_x_m=2.943e-6,
        n_steps=350,
        t_exp_per_step_s=5.0,
        dual_output=False,
        strategy="probabilistic",
        R_energy_ref=1.0e6,
        apodization="none",
    )
    source = load_template("stellar_g2v", sigma_grid_cm=config.sigma_grid(), magnitude=20.0, band="r")
    result = snr_from_time(source, config, config.total_observing_time_s)
    wavelength_nm = result.wavelength_nm[::-1]
    snr_curve = result.snr[::-1]

    fig, ax = plt.subplots(figsize=(10, 4.5), constrained_layout=True)
    ax.plot(wavelength_nm, snr_curve, linewidth=1.5, color="tab:purple")
    for ref_nm in [650.0, 656.3, 672.0]:
        ref_snr = float(np.interp(ref_nm, wavelength_nm, snr_curve))
        ax.scatter([ref_nm], [ref_snr], color="black", zorder=3)
        ax.annotate(f"{ref_nm:.1f} nm: {ref_snr:.2f}", (ref_nm, ref_snr), textcoords="offset points", xytext=(4, 8))
    _style_axes(ax, "SITELLE SN3-like Benchmark Curve", "Wavelength [nm]", "Analytical SNR")
    _save(fig, "05_sitelle_sn3_benchmark.png")


def write_summary_files(optimized: list[dict[str, float | str]]) -> None:
    manifest = OUTPUT_DIR / "README_generated_legacy.md"
    manifest.write_text(
        "\n".join(
            [
                "# Thesis Figure Outputs",
                "",
                "- `01_input_conditions_hii.png`: intrinsic HII-region source spectrum plus detector-entering source/sky/total photon rates.",
                "- `02_output_recovery_hii.png`: normalized recovered full-simulation spectrum overlaid on the truth, plus analytical SNR.",
                "- `03_strategy_comparison.png`: SNR ratio of probabilistic to hard-cut order sorting for three source classes and several MKID energy resolutions.",
                "- `04_config_optimization.png`: SNR heatmaps versus `delta_x_m` and `n_steps`, with the best grid point highlighted for each science case.",
                "- `05_sitelle_sn3_benchmark.png`: SN3-like conventional imaging-FTS benchmark SNR curve for manual comparison against the public SITELLE ETC.",
                "- `science_recommendations.csv`: compact table of preferred strategy, `R_E`, and scan configuration for the three science cases.",
            ]
        ),
        encoding="utf-8",
    )

    csv_path = OUTPUT_DIR / "science_recommendations.csv"
    fieldnames = [
        "science_case",
        "reference_wavelength_nm",
        "preferred_strategy",
        "preferred_R_energy",
        "best_n_steps",
        "best_delta_x_m",
        "best_reference_snr",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in optimized:
            writer.writerow(row)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    make_input_conditions()
    make_end_to_end_output()
    recommendations = make_strategy_comparison()
    optimized = make_config_optimization(recommendations)
    make_sitelle_benchmark()
    write_summary_files(optimized)
    print("Note: this script produces supplementary/legacy outputs and does not define the canonical 00-03 figures.")


if __name__ == "__main__":
    main()
