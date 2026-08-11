"""Generate two clean, validated thesis figures."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from mkid_ifts_sim import InstrumentConfig, Spectrum, run_full_simulation, load_template
from mkid_ifts_sim.order_sorting import contamination_fraction, grey_zone_loss

OUTPUT = Path(__file__).resolve().parents[1] / "outputs" / "canonical_figures"
OUTPUT.mkdir(parents=True, exist_ok=True)
E_PER_SIGMA_CM = 1.239841984e-4


def figure_order_sorting_performance() -> None:
    R_E = np.linspace(3, 120, 500)
    # Use a physically grounded representative order width from a reference scan setup.
    reference_cfg = InstrumentConfig(delta_x_m=2.0e-6)
    w = reference_cfg.free_spectral_range_cm * E_PER_SIGMA_CM

    contam = np.array([contamination_fraction(r, w) for r in R_E])
    loss_k1 = np.array([grey_zone_loss(r, w, 1.0) for r in R_E])
    loss_k2 = np.array([grey_zone_loss(r, w, 2.0) for r in R_E])
    loss_k3 = np.array([grey_zone_loss(r, w, 3.0) for r in R_E])

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)

    # --- Left panel: probabilistic contamination ---
    ax = axes[0]
    ax.plot(R_E, contam * 100, color="#2176AE", linewidth=2.2)
    ax.axhline(1, color="grey", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.axhline(5, color="grey", linestyle=":", linewidth=0.8, alpha=0.5)
    ax.set_xlabel(r"MKID Energy Resolving Power $R_E$", fontsize=12)
    ax.set_ylabel("Order Cross-Contamination [%]", fontsize=12)
    ax.set_title("Strategy 2: Probabilistic Weighting", fontsize=13)
    ax.set_xlim(3, 120)
    ax.set_ylim(0, 35)
    ax.grid(True, alpha=0.2)
    ax.text(
        0.03,
        0.95,
        rf"Representative order width: {w:.3f} eV",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        color="#666666",
    )

    r_1pct = float(R_E[np.argmin(np.abs(contam - 0.01))])
    r_5pct = float(R_E[np.argmin(np.abs(contam - 0.05))])
    ax.annotate(
        f"1% @ $R_E \\approx$ {r_1pct:.0f}",
        xy=(r_1pct, 1), xytext=(r_1pct + 25, 6),
        fontsize=9, color="grey",
        arrowprops=dict(arrowstyle="->", color="grey", lw=1.0),
    )
    ax.annotate(
        f"5% @ $R_E \\approx$ {r_5pct:.0f}",
        xy=(r_5pct, 5), xytext=(r_5pct + 18, 14),
        fontsize=9, color="grey",
        arrowprops=dict(arrowstyle="->", color="grey", lw=1.0),
    )

    # --- Right panel: hard-cut photon loss ---
    ax = axes[1]
    ax.plot(R_E, loss_k1 * 100, linewidth=2.2, label=r"$k_\sigma = 1.0$", color="#57A773")
    ax.plot(R_E, loss_k2 * 100, linewidth=2.2, label=r"$k_\sigma = 2.0$", color="#D76A03")
    ax.plot(R_E, loss_k3 * 100, linewidth=2.2, label=r"$k_\sigma = 3.0$", color="#BF1363")
    ax.set_xlabel(r"MKID Energy Resolving Power $R_E$", fontsize=12)
    ax.set_ylabel("Grey-Zone Photon Loss [%]", fontsize=12)
    ax.set_title("Strategy 1: Hard-Cut Filtering", fontsize=13)
    ax.set_xlim(3, 120)
    ax.set_ylim(0, 85)
    ax.grid(True, alpha=0.2)
    ax.legend(fontsize=11, framealpha=0.9, loc="upper right")

    fig.savefig(OUTPUT / "02_order_sorting_performance.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    print("  Saved: 02_order_sorting_performance.png")


def figure_fts_demonstration() -> None:
    """Single-order FTS round-trip: input lines -> interferogram -> recovered spectrum.

    Uses run_full_simulation with perfect order sorting (R_E=1e6) and a narrow
    spectral band containing the Halpha + [NII] + [SII] cluster.  This is
    the same regime validated by the monochromatic sinc test.
    """
    from mkid_ifts_sim.ifts import opd_positions

    # Config: step size gives sigma_nyquist=8000 cm-1, so the 14000-16000
    # band sits entirely within one folding order.  512 steps give spectral
    # resolution ~15.6 cm-1 => R~1000 at Halpha, enough to fully resolve
    # the Halpha/[NII] doublet (separation ~62 cm-1).
    cfg = InstrumentConfig(
        n_steps=512,
        n_sigma=4096,
        delta_x_m=6.25e-7,
        zpd_fraction=0.5,
        sigma_min_cm=14_000.0,
        sigma_max_cm=16_000.0,
        R_energy_ref=1.0e6,
        apodization="hanning",
        airmass=0.0,
        dual_output=True,
        strategy="probabilistic",
    )
    sigma = cfg.sigma_grid()
    order_idx = int(np.floor(np.mean([cfg.sigma_min_cm, cfg.sigma_max_cm]) / cfg.free_spectral_range_cm))
    wavelength_nm = 1.0e7 / sigma

    ha = 1.0e7 / 656.3
    nii_a = 1.0e7 / 654.8
    nii_b = 1.0e7 / 658.3
    sii_a = 1.0e7 / 671.6
    sii_b = 1.0e7 / 673.1

    lw = 3.0  # cm^-1 line width (~60 km/s at Halpha)
    flux = (
        1.0e5 * np.exp(-0.5 * ((sigma - ha) / lw) ** 2)
        + 1.8e4 * np.exp(-0.5 * ((sigma - nii_a) / lw) ** 2)
        + 5.5e4 * np.exp(-0.5 * ((sigma - nii_b) / lw) ** 2)
        + 3.0e4 * np.exp(-0.5 * ((sigma - sii_a) / lw) ** 2)
        + 2.5e4 * np.exp(-0.5 * ((sigma - sii_b) / lw) ** 2)
    )

    source = Spectrum(sigma, flux)
    result = run_full_simulation(source, cfg, include_noise=False, include_sky=False)

    recovered = result.stitched_spectrum
    rec_wl = recovered.wavelength_nm[::-1]
    rec_flux = recovered.flux_photons_per_s_cm2_nm[::-1]

    # Also run with no apodization for comparison
    cfg_unapod = cfg.with_updates(apodization="none")
    result_unapod = run_full_simulation(source, cfg_unapod, include_noise=False, include_sky=False)
    rec_unapod = result_unapod.stitched_spectrum
    rec_wl_u = rec_unapod.wavelength_nm[::-1]
    rec_flux_u = rec_unapod.flux_photons_per_s_cm2_nm[::-1]

    opd = opd_positions(cfg)
    igram = result.order_interferograms[0]

    # Normalize
    input_norm = flux[::-1] / np.max(flux)
    rec_norm = rec_flux / np.max(np.abs(rec_flux))
    rec_norm_u = rec_flux_u / np.max(np.abs(rec_flux_u))

    # Plotting
    fig, axes = plt.subplots(3, 1, figsize=(11, 9.5), constrained_layout=True)

    # --- (a) Input spectrum ---
    ax = axes[0]
    ax.plot(wavelength_nm[::-1], input_norm, color="#2176AE", linewidth=1.8)
    ax.set_ylabel("Normalized Flux", fontsize=11)
    ax.set_title(
        r"(a)  Input Spectrum: H$\alpha$ + [NII] + [SII] Emission-Line Cluster",
        fontsize=12, loc="left",
    )
    ax.set_xlim(630, 690)
    ax.set_ylim(-0.02, 1.12)
    ax.grid(True, alpha=0.2)
    labels = [
        (r"[NII] 654.8", 654.8), (r"H$\alpha$ 656.3", 656.3),
        (r"[NII] 658.3", 658.3), (r"[SII] 671.6", 671.6), (r"[SII] 673.1", 673.1),
    ]
    for text, lam in labels:
        idx = np.argmin(np.abs(wavelength_nm[::-1] - lam))
        ax.annotate(
            text, xy=(lam, input_norm[idx]),
            xytext=(0, 10), textcoords="offset points",
            fontsize=8, ha="center", color="#2176AE",
        )

    # --- (b) Interferogram ---
    ax = axes[1]
    ax.plot(opd * 1e3, igram, color="#444444", linewidth=0.4)
    ax.set_xlabel("Optical Path Difference [mm]", fontsize=11)
    ax.set_ylabel("Signal [arb.]", fontsize=11)
    ax.set_title(
        rf"(b)  Science Interferogram (dual-output difference, folding order {order_idx})",
        fontsize=12, loc="left",
    )
    ax.axvline(0, color="red", linestyle="--", linewidth=0.8, alpha=0.6, label="ZPD")
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(True, alpha=0.2)

    # --- (c) Recovered vs truth ---
    ax = axes[2]
    ax.plot(wavelength_nm[::-1], input_norm, color="#2176AE", linewidth=2.2,
            label="Input (truth)", zorder=3, alpha=0.6)
    ax.plot(rec_wl_u, rec_norm_u, color="#D76A03", linewidth=0.9,
            label="Recovered (no apodization)", alpha=0.65)
    ax.plot(rec_wl, rec_norm, color="#57A773", linewidth=1.6,
            label="Recovered (Hanning)", zorder=2)
    ax.set_xlabel("Wavelength [nm]", fontsize=11)
    ax.set_ylabel("Normalized Flux", fontsize=11)
    ax.set_title("(c)  FFT-Recovered Spectrum vs Input Truth", fontsize=12, loc="left")
    ax.set_xlim(630, 690)
    ax.set_ylim(-0.18, 1.15)
    ax.legend(fontsize=9.5, loc="upper right")
    ax.grid(True, alpha=0.2)

    fig.savefig(OUTPUT / "01_fts_signal_chain.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    input_wl = wavelength_nm[::-1]
    input_norm_local = flux[::-1] / max(np.max(flux), 1.0e-30)
    rec_interp = np.interp(input_wl, rec_wl, rec_norm, left=0.0, right=0.0)
    corr = np.corrcoef(input_norm_local, rec_interp)[0, 1]
    line_window = (input_wl > 652.0) & (input_wl < 660.0)
    input_ha_nm = float(input_wl[line_window][np.argmax(input_norm_local[line_window])])
    rec_ha_nm = float(input_wl[line_window][np.argmax(rec_interp[line_window])])
    resolution = cfg.sigma_nyquist_cm / cfg.n_steps
    print(f"  Saved: 01_fts_signal_chain.png")
    print(f"  Halpha window peak: input={input_ha_nm:.2f} nm  recovered={rec_ha_nm:.2f} nm")
    print(f"  Input/recovered correlation: r={corr:.3f}  (spectral bin = {resolution:.1f} cm-1)")
    print(f"  Folding order shown: {order_idx}  (FSR = {cfg.free_spectral_range_cm:.0f} cm-1)")


if __name__ == "__main__":
    print("Generating usable thesis figures...")
    figure_order_sorting_performance()
    figure_fts_demonstration()
    print("Done.")
