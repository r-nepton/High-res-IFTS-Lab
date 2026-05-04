"""Named presets for quick exploration (sources + partial configs)."""

from __future__ import annotations

from typing import Any


PRESETS: list[dict[str, Any]] = [
    {
        "id": "stellar_g2v_r20",
        "label": "Stellar G2V, r=20",
        "description": "Solar-like stellar template normalized to r=20 AB magnitude.",
        "source": {"mode": "point", "spectral_type": "stellar_g2v", "magnitude": 20.0, "band": "r"},
        "config": {},
    },
    {
        "id": "hii_region_default",
        "label": "HII region (template)",
        "description": "Emission-line cluster template suitable for H-alpha regime trades.",
        "source": {"mode": "point", "spectral_type": "hii_region", "magnitude": 22.0, "band": "r", "line_flux": 0.02},
        "config": {"strategy": "probabilistic", "R_energy_ref": 40.0},
    },
    {
        "id": "faint_galaxy_extended",
        "label": "Faint galaxy (extended)",
        "description": "Composite galaxy template as extended source.",
        "source": {"mode": "extended", "template": "composite_galaxy", "surface_brightness": 22.0, "band": "r"},
        "config": {"strategy": "probabilistic", "delta_x_m": 2e-6, "n_steps": 512, "t_exp_per_step_s": 2.0},
    },
    {
        "id": "planetary_nebula",
        "label": "Planetary nebula lines",
        "description": "Bright-line PN-style emission template.",
        "source": {"mode": "point", "spectral_type": "planetary_nebula", "magnitude": 18.0, "band": "r"},
        "config": {"strategy": "hard_cut", "k_sigma": 2.0, "R_energy_ref": 40.0},
    },
]
