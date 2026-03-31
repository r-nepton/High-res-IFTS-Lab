from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from pathlib import Path
import json
from typing import Any, Mapping

import numpy as np
import yaml


_VALID_COATINGS = {"aluminum", "silver"}
_VALID_SCALINGS = {"sqrt", "linear", "flat"}
_VALID_STRATEGIES = {"hard_cut", "probabilistic"}
_VALID_APODIZATIONS = {"none", "norton-beer", "gaussian", "hanning"}
_VALID_PHASE_METHODS = {"mertz", "forman"}
_VALID_MOON_PHASES = {"new", "crescent", "quarter", "full"}


@dataclass(slots=True)
class InstrumentConfig:
    # Telescope
    D_primary: float = 3.6
    obscuration: float = 0.12
    altitude_m: float = 4200.0
    n_reflections: int = 3
    mirror_coating: str = "silver"

    # IFTS
    delta_x_m: float = 2.0e-6
    n_steps: int = 2048
    zpd_fraction: float = 0.10
    opd_jitter_rms_m: float = 0.0
    dual_output: bool = True
    optical_transmission: float = 0.88
    beamsplitter_ratio: float = 0.50

    # MKID
    R_energy_ref: float = 40.0
    R_energy_ref_nm: float = 500.0
    R_energy_scaling: str = "sqrt"
    qe_model: str = "baseline"
    dead_time_us: float = 10.0
    max_count_rate_hz: float = 5_000.0
    dark_rate_hz: float = 0.0

    # Observation
    t_exp_per_step_s: float = 1.0
    n_pixels: int = 1
    airmass: float = 1.2
    moon_phase: str = "new"
    use_nd_filter: bool = False
    nd_transmission: float = 0.1
    pixel_scale_arcsec: float = 0.2
    pwv_mm: float = 2.5
    ambient_temp_k: float = 273.0
    thermal_emissivity: float = 0.08

    # Order separation
    strategy: str = "probabilistic"
    k_sigma: float = 2.0

    # Processing
    apodization: str = "hanning"
    phase_method: str = "mertz"

    # Internal spectral grid
    sigma_min_cm: float = 9091.0
    sigma_max_cm: float = 28571.0
    n_sigma: int = 4096
    random_seed: int = 12345

    def __post_init__(self) -> None:
        if self.D_primary <= 0:
            raise ValueError("D_primary must be positive.")
        if not 0 <= self.obscuration < 1:
            raise ValueError("obscuration must be in [0, 1).")
        if self.n_reflections < 1:
            raise ValueError("n_reflections must be >= 1.")
        if self.mirror_coating not in _VALID_COATINGS:
            raise ValueError(f"mirror_coating must be one of {_VALID_COATINGS}.")
        if self.delta_x_m <= 0:
            raise ValueError("delta_x_m must be positive.")
        if self.n_steps < 16:
            raise ValueError("n_steps must be >= 16.")
        if not 0 < self.zpd_fraction < 1:
            raise ValueError("zpd_fraction must be in (0, 1).")
        if self.opd_jitter_rms_m < 0:
            raise ValueError("opd_jitter_rms_m must be non-negative.")
        if self.R_energy_ref <= 0 or self.R_energy_ref_nm <= 0:
            raise ValueError("R_energy_ref and R_energy_ref_nm must be positive.")
        if self.R_energy_scaling not in _VALID_SCALINGS:
            raise ValueError(f"R_energy_scaling must be one of {_VALID_SCALINGS}.")
        if self.dead_time_us < 0 or self.max_count_rate_hz <= 0 or self.dark_rate_hz < 0:
            raise ValueError("Detector rates and dead time must be physically valid.")
        if self.t_exp_per_step_s <= 0:
            raise ValueError("t_exp_per_step_s must be positive.")
        if self.n_pixels < 1:
            raise ValueError("n_pixels must be >= 1.")
        if self.moon_phase not in _VALID_MOON_PHASES:
            raise ValueError(f"moon_phase must be one of {_VALID_MOON_PHASES}.")
        if self.use_nd_filter and not 0 < self.nd_transmission <= 1:
            raise ValueError("nd_transmission must be in (0, 1] when ND filter is enabled.")
        if self.strategy not in _VALID_STRATEGIES:
            raise ValueError(f"strategy must be one of {_VALID_STRATEGIES}.")
        if self.k_sigma < 0:
            raise ValueError("k_sigma must be non-negative.")
        if self.apodization not in _VALID_APODIZATIONS:
            raise ValueError(f"apodization must be one of {_VALID_APODIZATIONS}.")
        if self.phase_method not in _VALID_PHASE_METHODS:
            raise ValueError(f"phase_method must be one of {_VALID_PHASE_METHODS}.")
        if self.sigma_min_cm <= 0 or self.sigma_max_cm <= self.sigma_min_cm:
            raise ValueError("sigma grid limits must satisfy 0 < min < max.")
        if self.n_sigma < 128:
            raise ValueError("n_sigma must be >= 128.")

    @property
    def zpd_index(self) -> int:
        return int(round(self.zpd_fraction * (self.n_steps - 1)))

    @property
    def total_observing_time_s(self) -> float:
        return self.n_steps * self.t_exp_per_step_s

    @property
    def delta_x_cm(self) -> float:
        return self.delta_x_m * 100.0

    @property
    def sigma_nyquist_cm(self) -> float:
        return 1.0 / (2.0 * self.delta_x_cm)

    @property
    def free_spectral_range_cm(self) -> float:
        return self.sigma_nyquist_cm

    def sigma_grid(self) -> np.ndarray:
        return np.linspace(self.sigma_min_cm, self.sigma_max_cm, self.n_sigma)

    def wavelength_grid_nm(self) -> np.ndarray:
        return 1.0e7 / self.sigma_grid()

    def with_updates(self, **updates: Any) -> "InstrumentConfig":
        return replace(self, **updates)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> "InstrumentConfig":
        return cls(**dict(mapping))

    @classmethod
    def from_file(cls, path: str | Path) -> "InstrumentConfig":
        payload = _read_serialized_mapping(path)
        return cls.from_mapping(payload)


def _read_serialized_mapping(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix == ".json":
        return json.loads(file_path.read_text(encoding="utf-8"))
    if suffix in {".yml", ".yaml"}:
        return yaml.safe_load(file_path.read_text(encoding="utf-8"))
    raise ValueError(f"Unsupported configuration file format: {suffix}")
