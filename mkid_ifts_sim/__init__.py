from .config import InstrumentConfig
from .source import Spectrum, apply_redshift, blackbody, emission_lines, from_file, load_template, make_input_source
from .atmosphere import transmission
from .sky_background import oh_lines, sky_spectrum, thermal_background
from .telescope import ThroughputResult, collecting_area, mirror_reflectivity, throughput, throughput_components
from .ifts import (
    InterferogramResult,
    OrderLayout,
    add_photon_noise,
    combine_dual_output,
    fold_sigma_to_local,
    folding_orders,
    generate_interferogram,
    modulation_matrix,
    modulation_efficiency,
    optics_transmission,
    opd_positions,
    unfold_local_sigma,
)
from .mkid_detector import DetectorRateResult, apply_dead_time, apply_detector_response, check_saturation, energy_resolution, energy_sigma_eV, qe
from .order_sorting import (
    OrderSortingResult,
    assignment_probabilities,
    contamination_fraction,
    grey_zone_loss,
    hard_cut_assignment,
    monte_carlo_assignments,
    monte_carlo_order_statistics,
    probabilistic_assignment,
    sort_spectrum_into_orders,
)
from .spectrum_recovery import (
    RecoveredOrderSpectrum,
    apodize,
    fft_to_spectrum,
    phase_correction,
    recover_order_spectrum,
    remove_dc,
    stitch_orders,
)
from .snr import NoiseComponents, SNRResult, compute_snr, noise_breakdown
from .simulation import FullModeSNRComparison, FullSimulationResult, estimate_full_mode_snr, run_full_simulation


def prepare_observation(*args, **kwargs):
    from .etc import prepare_observation as _prepare_observation

    return _prepare_observation(*args, **kwargs)


def snr_from_time(*args, **kwargs):
    from .etc import snr_from_time as _snr_from_time

    return _snr_from_time(*args, **kwargs)


def time_from_snr(*args, **kwargs):
    from .etc import time_from_snr as _time_from_snr

    return _time_from_snr(*args, **kwargs)


def optimize_config(*args, **kwargs):
    from .etc import optimize_config as _optimize_config

    return _optimize_config(*args, **kwargs)

__all__ = [
    "InstrumentConfig",
    "Spectrum",
    "apply_redshift",
    "blackbody",
    "emission_lines",
    "from_file",
    "load_template",
    "make_input_source",
    "transmission",
    "oh_lines",
    "sky_spectrum",
    "thermal_background",
    "ThroughputResult",
    "collecting_area",
    "mirror_reflectivity",
    "throughput",
    "throughput_components",
    "InterferogramResult",
    "OrderLayout",
    "add_photon_noise",
    "combine_dual_output",
    "fold_sigma_to_local",
    "folding_orders",
    "generate_interferogram",
    "modulation_matrix",
    "modulation_efficiency",
    "optics_transmission",
    "opd_positions",
    "unfold_local_sigma",
    "DetectorRateResult",
    "apply_dead_time",
    "apply_detector_response",
    "check_saturation",
    "energy_resolution",
    "energy_sigma_eV",
    "qe",
    "OrderSortingResult",
    "assignment_probabilities",
    "contamination_fraction",
    "grey_zone_loss",
    "hard_cut_assignment",
    "monte_carlo_assignments",
    "monte_carlo_order_statistics",
    "probabilistic_assignment",
    "sort_spectrum_into_orders",
    "RecoveredOrderSpectrum",
    "apodize",
    "fft_to_spectrum",
    "phase_correction",
    "recover_order_spectrum",
    "remove_dc",
    "stitch_orders",
    "NoiseComponents",
    "SNRResult",
    "compute_snr",
    "noise_breakdown",
    "FullModeSNRComparison",
    "FullSimulationResult",
    "estimate_full_mode_snr",
    "run_full_simulation",
    "optimize_config",
    "prepare_observation",
    "snr_from_time",
    "time_from_snr",
]
