"""Generate a clean pipeline/signal-chain diagram for the MKID-IFTS simulator."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUTPUT = Path(__file__).resolve().parents[1] / "outputs" / "canonical_figures"
OUTPUT.mkdir(parents=True, exist_ok=True)

# --- Layout constants ---
BOX_W = 2.6
BOX_H = 0.72
GAP_Y = 1.18
COL_X = [1.8, 6.2]  # two columns

STAGES = [
    # (label, subtitle, column, row, color)
    ("Astrophysical\nSource", r"$S(\lambda)$  [phot/s/cm²/nm]", 0, 0, "#2176AE"),
    ("Atmosphere", r"$\times\, T_{\rm atm}(\lambda,\, X)$", 0, 1, "#2176AE"),
    ("Sky\nBackground", r"$+\, B_{\rm sky}(\lambda)$  (OH, moonlight, thermal)", 0, 2, "#2176AE"),
    ("Telescope", r"$\times\, A_{\rm eff}\, R_{\rm mirror}^{\,n}$", 0, 3, "#2176AE"),
    ("IFTS Optics &\nInterferogram", "Modulation matrix,  dual-output ports", 0, 4, "#5B3A8C"),
    ("MKID\nDetection", r"QE,  energy tag $E \pm \sigma_E$,  dead time", 1, 4, "#5B3A8C"),
    ("Order\nSeparation", "Hard-cut  or  probabilistic weighting", 1, 3, "#BF1363"),
    ("Spectrum\nRecovery", "DC removal,  phase correction,  FFT,  stitch", 1, 2, "#BF1363"),
    ("SNR &\nNoise Budget", "Source + sky distributed + contamination", 1, 1, "#57A773"),
    ("Exposure Time\nCalculator", r"$t_{\rm obs}$  for target SNR  &  config optimization", 1, 0, "#57A773"),
]

ARROWS = [
    # (from_idx, to_idx)
    (0, 1), (1, 2), (2, 3), (3, 4),  # left column down
    (4, 5),  # across bottom
    (5, 6), (6, 7), (7, 8), (8, 9),  # right column up
]


def _box_center(col: int, row: int) -> tuple[float, float]:
    x = COL_X[col]
    y = 4.5 - row * GAP_Y
    return x, y


def main() -> None:
    fig, ax = plt.subplots(figsize=(9.5, 7.2))
    ax.set_xlim(-0.2, 9.7)
    ax.set_ylim(-1.3, 5.7)
    ax.set_aspect("equal")
    ax.axis("off")

    centers: list[tuple[float, float]] = []

    for i, (label, subtitle, col, row, color) in enumerate(STAGES):
        cx, cy = _box_center(col, row)
        centers.append((cx, cy))

        box = FancyBboxPatch(
            (cx - BOX_W / 2, cy - BOX_H / 2), BOX_W, BOX_H,
            boxstyle="round,pad=0.12",
            facecolor=color, edgecolor="white", linewidth=2.0, alpha=0.88,
        )
        ax.add_patch(box)
        ax.text(cx, cy + 0.07, label, ha="center", va="center",
                fontsize=9.5, fontweight="bold", color="white", linespacing=1.15)
        ax.text(cx, cy - 0.28, subtitle, ha="center", va="center",
                fontsize=6.8, color="white", alpha=0.92, style="italic")

    # Draw arrows
    for from_idx, to_idx in ARROWS:
        x0, y0 = centers[from_idx]
        x1, y1 = centers[to_idx]

        # Compute connection points on box edges
        if x0 == x1:  # vertical
            if y0 > y1:
                y0 -= BOX_H / 2
                y1 += BOX_H / 2
            else:
                y0 += BOX_H / 2
                y1 -= BOX_H / 2
        else:  # horizontal
            if x0 < x1:
                x0 += BOX_W / 2
                x1 -= BOX_W / 2
            else:
                x0 -= BOX_W / 2
                x1 += BOX_W / 2

        arrow = FancyArrowPatch(
            (x0, y0), (x1, y1),
            arrowstyle="->,head_width=5,head_length=4",
            connectionstyle="arc3,rad=0.0",
            color="#333333", linewidth=1.6,
        )
        ax.add_patch(arrow)

    # Column labels
    ax.text(COL_X[0], 5.35, "Signal Propagation", ha="center",
            fontsize=11, fontweight="bold", color="#444")
    ax.text(COL_X[1], 5.35, "Data Reduction", ha="center",
            fontsize=11, fontweight="bold", color="#444")

    # Downward / upward arrows as column flow indicators
    ax.annotate("", xy=(COL_X[0] - 1.6, -0.6), xytext=(COL_X[0] - 1.6, 5.0),
                arrowprops=dict(arrowstyle="->, head_width=0.3", color="#ccc", lw=2))
    ax.annotate("", xy=(COL_X[1] + 1.6, 5.0), xytext=(COL_X[1] + 1.6, -0.6),
                arrowprops=dict(arrowstyle="->, head_width=0.3", color="#ccc", lw=2))

    # Module labels on the side
    module_labels = [
        (0, "source.py"), (1, "atmosphere.py"), (2, "sky_background.py"),
        (3, "telescope.py"), (4, "ifts.py"), (5, "mkid_detector.py"),
        (6, "order_sorting.py"), (7, "spectrum_recovery.py"),
        (8, "snr.py"), (9, "etc.py"),
    ]
    for idx, mod_name in module_labels:
        cx, cy = centers[idx]
        col = STAGES[idx][2]
        if col == 0:
            ax.text(cx - BOX_W / 2 - 0.12, cy, mod_name, ha="right", va="center",
                    fontsize=6.5, color="#999", family="monospace")
        else:
            ax.text(cx + BOX_W / 2 + 0.12, cy, mod_name, ha="left", va="center",
                    fontsize=6.5, color="#999", family="monospace")

    fig.savefig(OUTPUT / "00_pipeline_overview.png", dpi=220, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    print("Saved: 00_pipeline_overview.png")


if __name__ == "__main__":
    main()
