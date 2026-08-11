export type SourceMode = "point" | "extended";
export type Strategy = "probabilistic" | "hard_cut";

export interface SourcePayload {
  mode: SourceMode;
  spectral_type?: string;
  magnitude?: number;
  band?: string;
  template?: string;
  surface_brightness?: number;
  line_flux?: number | null;
}

export interface InstrumentPayload {
  n_steps?: number;
  delta_x_m?: number;
  t_exp_per_step_s?: number;
  n_sigma?: number;
  airmass?: number;
  moon_phase?: string;
  pwv_mm?: number;
  ambient_temp_k?: number;
  thermal_emissivity?: number;
  D_primary?: number;
  mirror_coating?: string;
  n_reflections?: number;
  optical_transmission?: number;
  n_pixels?: number;
  R_energy_ref?: number;
  R_energy_ref_nm?: number;
  R_energy_scaling?: string;
  qe_model?: string;
  calibration_profile?: "parametric" | "tables";
  strategy?: Strategy;
  k_sigma?: number;
  apodization?: string;
  phase_method?: string;
}

export interface Preset {
  id: string;
  label: string;
  description: string;
  source: SourcePayload;
  config: InstrumentPayload;
}

export interface SeriesPayload {
  wavelength_nm: number[];
  snr?: number[];
  source_rate_per_nm?: number[];
  sky_rate_per_nm?: number[];
  total_rate_per_nm?: number[];
  system_throughput?: number[];
  ratio?: number[];
}

export interface SnrResponse {
  config_used: Record<string, number | string | boolean>;
  t_total_s: number;
  snr: SeriesPayload & {
    source_counts: number[];
    saturation_warning: boolean;
    noise?: Record<string, number[]>;
  };
  stats: {
    snr_max: number;
    snr_max_wavelength_nm: number;
  };
}

export interface RatesResponse {
  config_used: Record<string, number | string | boolean>;
  rates: SeriesPayload;
}

export interface StrategyResponse {
  hard_cut: SeriesPayload;
  probabilistic: SeriesPayload;
  ratio_prob_over_hard: SeriesPayload;
}
