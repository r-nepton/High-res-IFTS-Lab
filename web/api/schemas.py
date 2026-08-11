from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from web.api.limits import MAX_N_SIGMA, MAX_N_STEPS, MAX_T_TOTAL_S, MAX_TARGET_SNR, MIN_N_SIGMA, MIN_N_STEPS


class SourcePayload(BaseModel):
    """Source request compatible with make_input_source (no filesystem paths)."""

    model_config = ConfigDict(extra="forbid")

    mode: Literal["point", "extended"] = "point"
    spectral_type: str = "stellar_g2v"
    magnitude: float = Field(default=20.0, ge=-5.0, le=35.0)
    band: str = Field(default="r", pattern=r"^[ugriz]$")
    template: str = "composite_galaxy"
    surface_brightness: float = Field(default=21.0, ge=10.0, le=35.0)
    line_flux: float | None = Field(default=None, ge=0.0)


class InstrumentPayload(BaseModel):
    """Subset of InstrumentConfig exposed to the web API."""

    model_config = ConfigDict(extra="forbid")

    D_primary: float | None = Field(default=None, gt=0.0, le=50.0)
    obscuration: float | None = Field(default=None, ge=0.0, lt=1.0)
    altitude_m: float | None = Field(default=None, ge=0.0, le=9000.0)
    n_reflections: int | None = Field(default=None, ge=1, le=20)
    mirror_coating: Literal["aluminum", "silver"] | None = None

    delta_x_m: float | None = Field(default=None, gt=0.0, le=1e-2)
    n_steps: int | None = Field(default=None, ge=MIN_N_STEPS, le=MAX_N_STEPS)
    zpd_fraction: float | None = Field(default=None, gt=0.0, lt=1.0)
    opd_jitter_rms_m: float | None = Field(default=None, ge=0.0, le=1e-3)
    dual_output: bool | None = None
    optical_transmission: float | None = Field(default=None, gt=0.0, le=1.0)
    beamsplitter_ratio: float | None = Field(default=None, gt=0.0, lt=1.0)

    R_energy_ref: float | None = Field(default=None, gt=0.0, le=1000.0)
    R_energy_ref_nm: float | None = Field(default=None, gt=0.0, le=2000.0)
    R_energy_scaling: Literal["sqrt", "linear", "flat"] | None = None
    qe_model: Literal["baseline", "blue_optimized", "red_optimized"] | None = None
    calibration_profile: Literal["parametric", "tables"] | None = None
    dead_time_us: float | None = Field(default=None, ge=0.0, le=1000.0)
    max_count_rate_hz: float | None = Field(default=None, gt=0.0, le=1e9)
    dark_rate_hz: float | None = Field(default=None, ge=0.0, le=1e9)

    t_exp_per_step_s: float | None = Field(default=None, gt=0.0, le=3600.0)
    n_pixels: int | None = Field(default=None, ge=1, le=1_000_000)
    airmass: float | None = Field(default=None, ge=0.0, le=10.0)
    moon_phase: Literal["new", "crescent", "quarter", "full"] | None = None
    use_nd_filter: bool | None = None
    nd_transmission: float | None = Field(default=None, gt=0.0, le=1.0)
    pixel_scale_arcsec: float | None = Field(default=None, gt=0.0, le=10.0)
    pwv_mm: float | None = Field(default=None, ge=0.0, le=50.0)
    ambient_temp_k: float | None = Field(default=None, gt=0.0, le=400.0)
    thermal_emissivity: float | None = Field(default=None, ge=0.0, le=1.0)

    strategy: Literal["hard_cut", "probabilistic"] | None = None
    k_sigma: float | None = Field(default=None, ge=0.0, le=10.0)

    apodization: Literal["none", "norton-beer", "gaussian", "hanning"] | None = None
    phase_method: Literal["mertz", "forman"] | None = None

    sigma_min_cm: float | None = Field(default=None, gt=0.0, le=100_000.0)
    sigma_max_cm: float | None = Field(default=None, gt=0.0, le=100_000.0)
    n_sigma: int | None = Field(default=None, ge=MIN_N_SIGMA, le=MAX_N_SIGMA)
    random_seed: int | None = None

    @model_validator(mode="after")
    def _sigma_bounds(self) -> InstrumentPayload:
        if self.sigma_min_cm is not None and self.sigma_max_cm is not None:
            if self.sigma_max_cm <= self.sigma_min_cm:
                raise ValueError("sigma_max_cm must exceed sigma_min_cm")
        return self


class SnrFromTimeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: SourcePayload = Field(default_factory=SourcePayload)
    config: InstrumentPayload = Field(default_factory=InstrumentPayload)
    t_total_s: float = Field(gt=0.0, le=MAX_T_TOTAL_S)


class TimeFromSnrRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: SourcePayload = Field(default_factory=SourcePayload)
    config: InstrumentPayload = Field(default_factory=InstrumentPayload)
    target_snr: float = Field(gt=0.0, le=MAX_TARGET_SNR)
    ref_nm: float = Field(gt=100.0, lt=5000.0)


class ScienceGoalPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ref_nm: float = Field(default=656.3, gt=100.0, lt=5000.0)
    target_snr: float = Field(default=10.0, gt=0.0, le=MAX_TARGET_SNR)
    target_resolution: float = Field(default=3000.0, gt=0.0, le=200_000.0)
    max_time_s: float = Field(default=3600.0, gt=0.0, le=MAX_T_TOTAL_S)


class OptimizeConfigRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: SourcePayload = Field(default_factory=SourcePayload)
    config: InstrumentPayload = Field(default_factory=InstrumentPayload)
    science_goal: ScienceGoalPayload = Field(default_factory=ScienceGoalPayload)


class ObservationRatesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: SourcePayload = Field(default_factory=SourcePayload)
    config: InstrumentPayload = Field(default_factory=InstrumentPayload)


class CompareStrategiesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: SourcePayload = Field(default_factory=SourcePayload)
    config: InstrumentPayload = Field(default_factory=InstrumentPayload)
    t_total_s: float = Field(gt=0.0, le=MAX_T_TOTAL_S)
