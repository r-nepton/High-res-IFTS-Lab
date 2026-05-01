"""Generate a clean Strategy 1 vs Strategy 2 comparison figure."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from mkid_ifts_sim import InstrumentConfig, load_template, snr_from_time

OUTPUT = Path(__file__).resolve().parents[1] / "outputs" / "thesis_figures"
OUTPUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    base_config = InstrumentConfig(
        n_steps=512,
        n_sigma=2048,
        delta_x_m=2.0e-6,
        t_exp_per_step_s=2.0,
        moon_phase="new",
        apodization="none",
        k_sigma=2.0,
    )
    r_e_sweep = np.array([10, 15, 20, 25, 30, 35, 40, 50, 60, 80, 100], dtype=float)
    sources = {
        r"HII Region (H$\alpha$ 656 nm)": {
            "source": load_template("hii_region", sigma_grid_cm=base_config.sigma_grid(), line_flux=2.0e-2),
            "ref_nm": 656.3,
            "color": "#2176AE",
            "marker": "o",
        },
        "Faint Galaxy (750 nm)": {
            "source": load_template("composite_galaxy", sigma_grid_cm=base_config.sigma_grid(), magnitude=22.0, band="r"),
            "ref_nm": 750.0,
            "color": "#D76A03",
            "marker": "s",
        },
        "Planetary Nebula ([OIII] 501 nm)": {
            "source": load_template("planetary_nebula", sigma_grid_cm=base_config.sigma_grid()),
            "ref_nm": 500.7,
            "color": "#57A773",
            "marker": "^",
        },
    }

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.5), constrained_layout=True)

    # --- Left panel: SNR ratio at reference wavelength vs R_E ---
    ax = axes[0]
    for label, info in sources.items():
        ratios = []
        for r_e in r_e_sweep:
            hard_cfg = base_config.with_updates(R_energy_ref=r_e, strategy="hard_cut")
            prob_cfg = base_config.with_updates(R_energy_ref=r_e, strategy="probabilistic")
            hard = snr_from_time(info["source"], hard_cfg, hard_cfg.total_observing_time_s)
            prob = snr_from_time(info["source"], prob_cfg, prob_cfg.total_observing_time_s)
            h = float(np.interp(info["ref_nm"], hard.wavelength_nm[::-1], hard.snr[::-1]))
            p = float(np.interp(info["ref_nm"], prob.wavelength_nm[::-1], prob.snr[::-1]))
            if h > 0.01:
                ratios.append(p / h)
            else:
                ratios.append(np.nan)
        ax.plot(r_e_sweep, ratios, color=info["color"], marker=info["marker"],
                markersize=5, linewidth=1.8, label=label)

    ax.axhline(1.0, color="black", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.set_xlabel(r"MKID Energy Resolving Power $R_E$", fontsize=12)
    ax.set_ylabel(r"SNR$_{\rm probabilistic}$ / SNR$_{\rm hard\text{-}cut}$", fontsize=12)
    ax.set_title("(a)  Strategy Comparison at Reference Wavelength", fontsize=12, loc="left")
    ax.set_xlim(8, 105)
    ax.set_ylim(0.5, 8.0)
    ax.fill_between([8, 105], 1.0, 0.5, alpha=0.06, color="red")
    ax.fill_between([8, 105], 1.0, 8.0, alpha=0.06, color="green")
    ax.text(90, 0.65, "Hard-cut\nbetter", fontsize=8.5, ha="center", color="#888", style="italic")
    ax.text(90, 5.5, "Probabilistic\nbetter", fontsize=8.5, ha="center", color="#888", style="italic")
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(True, alpha=0.2)

    # --- Right panel: Full SNR curves at R_E=40 for faint galaxy ---
    ax = axes[1]
    r_e_demo = 40.0
    hard_cfg = base_config.with_updates(R_energy_ref=r_e_demo, strategy="hard_cut")
    prob_cfg = base_config.with_updates(R_energy_ref=r_e_demo, strategy="probabilistic")
    galaxy = sources["Faint Galaxy (750 nm)"]["source"]
    hard = snr_from_time(galaxy, hard_cfg, hard_cfg.total_observing_time_s)
    prob = snr_from_time(galaxy, prob_cfg, prob_cfg.total_observing_time_s)

    wl = hard.wavelength_nm[::-1]
    ax.plot(wl, hard.snr[::-1], color="#BF1363", linewidth=1.6,
            label=f"Hard-cut ($k_\\sigma$=2.0)")
    ax.plot(wl, prob.snr[::-1], color="#2176AE", linewidth=1.6,
            label="Probabilistic")
    ax.set_xlabel("Wavelength [nm]", fontsize=12)
    ax.set_ylabel("SNR per spectral channel", fontsize=12)
    ax.set_title(
        f"(b)  Faint Galaxy SNR Curves ($R_E$ = {r_e_demo:.0f})",
        fontsize=12, loc="left",
    )
    ax.set_xlim(360, 1080)
    ax.legend(fontsize=10, loc="upper right")
    ax.grid(True, alpha=0.2)

    fig.suptitle(
        "Order-Sorting Strategy Comparison: Probabilistic Weighting vs Hard-Cut Filtering\n"
        f"({base_config.n_steps} steps, "
        r"$\Delta x$ = "
        f"{base_config.delta_x_m*1e6:.0f} "
        r"$\mu$m, "
        f"$k_\\sigma$ = {base_config.k_sigma:.1f}, "
        f"$t_{{\\rm obs}}$ = {base_config.total_observing_time_s:.0f} s, dark new-moon sky)",
        fontsize=11.5,
    )

    fig.savefig(OUTPUT / "03_strategy_comparison.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    print("Saved: 03_strategy_comparison.png")

    # Print summary
    print("\n=== SNR at reference wavelengths (R_E=40) ===")
    for label, info in sources.items():
        hard_cfg = base_config.with_updates(R_energy_ref=40.0, strategy="hard_cut")
        prob_cfg = base_config.with_updates(R_energy_ref=40.0, strategy="probabilistic")
        hard = snr_from_time(info["source"], hard_cfg, hard_cfg.total_observing_time_s)
        prob = snr_from_time(info["source"], prob_cfg, prob_cfg.total_observing_time_s)
        h = float(np.interp(info["ref_nm"], hard.wavelength_nm[::-1], hard.snr[::-1]))
        p = float(np.interp(info["ref_nm"], prob.wavelength_nm[::-1], prob.snr[::-1]))
        print(f"  {label:42s}: hard={h:8.2f}  prob={p:8.2f}  ratio={p/h if h > 0 else float('inf'):.2f}")


if __name__ == "__main__":
    main()
