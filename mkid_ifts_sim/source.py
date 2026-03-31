from __future__ import annotations

from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
import csv
from typing import Any, Mapping

import numpy as np
from astropy.io import fits
from scipy.constants import c, h, k

from .config import InstrumentConfig


BAND_CENTERS_NM = {
    "u": 365.0,
    "g": 477.0,
    "r": 623.0,
    "i": 763.0,
    "z": 905.0,
    "y": 1020.0,
    "v": 550.0,
}

LINE_WAVELENGTHS_NM = {
    "oii_3727": 372.7,
    "hbeta": 486.1,
    "oiii_4959": 495.9,
    "oiii_5007": 500.7,
    "nii_6548": 654.8,
    "ha": 656.3,
    "nii_6583": 658.3,
    "sii_6716": 671.6,
    "sii_6731": 673.1,
}


@dataclass(slots=True)
class Spectrum:
    sigma_cm: np.ndarray
    flux_photons_per_s_cm2_nm: np.ndarray
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.sigma_cm = np.asarray(self.sigma_cm, dtype=float)
        self.flux_photons_per_s_cm2_nm = np.asarray(self.flux_photons_per_s_cm2_nm, dtype=float)
        if self.sigma_cm.ndim != 1 or self.flux_photons_per_s_cm2_nm.ndim != 1:
            raise ValueError("Spectrum arrays must be one-dimensional.")
        if self.sigma_cm.size != self.flux_photons_per_s_cm2_nm.size:
            raise ValueError("Spectrum arrays must have the same length.")
        if np.any(np.diff(self.sigma_cm) <= 0):
            raise ValueError("sigma_cm must be strictly increasing.")

    @property
    def wavelength_nm(self) -> np.ndarray:
        return 1.0e7 / self.sigma_cm

    def copy(self) -> "Spectrum":
        return Spectrum(self.sigma_cm.copy(), self.flux_photons_per_s_cm2_nm.copy(), dict(self.meta))

    def resample(self, sigma_cm: np.ndarray) -> "Spectrum":
        sigma_cm = np.asarray(sigma_cm, dtype=float)
        lam_src = self.wavelength_nm[::-1]
        flux_src = self.flux_photons_per_s_cm2_nm[::-1]
        lam_out = (1.0e7 / sigma_cm)[::-1]
        flux_out = np.interp(lam_out, lam_src, flux_src, left=0.0, right=0.0)[::-1]
        return Spectrum(sigma_cm, flux_out, dict(self.meta))

    def integrated_flux(self) -> float:
        lam = self.wavelength_nm[::-1]
        flux = self.flux_photons_per_s_cm2_nm[::-1]
        return float(np.trapezoid(flux, lam))


def default_sigma_grid(config: InstrumentConfig | None = None) -> np.ndarray:
    if config is None:
        config = InstrumentConfig()
    return config.sigma_grid()


def ab_magnitude_to_photon_flux(wavelength_nm: float, magnitude: float) -> float:
    wavelength_cm = wavelength_nm * 1.0e-7
    c_cgs = c * 100.0
    h_cgs = h * 1.0e7
    f_nu = 3631.0e-23 * 10.0 ** (-0.4 * magnitude)
    f_lambda_cm = f_nu * c_cgs / wavelength_cm**2
    f_lambda_nm = f_lambda_cm * 1.0e-7
    photon_energy_erg = h_cgs * c_cgs / wavelength_cm
    return f_lambda_nm / photon_energy_erg


def normalize_to_ab_magnitude(spectrum: Spectrum, magnitude: float, band: str = "r") -> Spectrum:
    band_key = band.lower()
    if band_key not in BAND_CENTERS_NM:
        raise ValueError(f"Unknown photometric band: {band}")
    lam_ref = BAND_CENTERS_NM[band_key]
    current = np.interp(lam_ref, spectrum.wavelength_nm[::-1], spectrum.flux_photons_per_s_cm2_nm[::-1])
    target = ab_magnitude_to_photon_flux(lam_ref, magnitude)
    scale = 0.0 if current <= 0 else target / current
    return Spectrum(
        spectrum.sigma_cm,
        spectrum.flux_photons_per_s_cm2_nm * scale,
        {**spectrum.meta, "ab_magnitude": magnitude, "band": band_key},
    )


def blackbody(
    T_eff: float,
    mag: float,
    band: str = "r",
    sigma_grid_cm: np.ndarray | None = None,
) -> Spectrum:
    sigma_grid_cm = default_sigma_grid() if sigma_grid_cm is None else np.asarray(sigma_grid_cm, dtype=float)
    wavelength_nm = 1.0e7 / sigma_grid_cm
    wavelength_m = wavelength_nm * 1.0e-9
    exponent = (h * c) / (wavelength_m * k * T_eff)
    b_lambda = (2.0 * h * c**2) / (wavelength_m**5) / np.expm1(exponent)
    raw = Spectrum(sigma_grid_cm, b_lambda / np.max(b_lambda), {"template": "blackbody", "T_eff": T_eff})
    return normalize_to_ab_magnitude(raw, mag, band)


def emission_lines(
    lines_dict: Mapping[str | float, float],
    fwhm_kms: float = 100.0,
    sigma_grid_cm: np.ndarray | None = None,
    continuum_level: float = 0.0,
) -> Spectrum:
    sigma_grid_cm = default_sigma_grid() if sigma_grid_cm is None else np.asarray(sigma_grid_cm, dtype=float)
    wavelength_nm = 1.0e7 / sigma_grid_cm
    flux = np.full_like(wavelength_nm, fill_value=float(continuum_level), dtype=float)
    c_kms = c / 1000.0
    for key, integrated_line_flux in lines_dict.items():
        lam0 = float(LINE_WAVELENGTHS_NM.get(str(key).lower(), key))
        sigma_nm = (lam0 * fwhm_kms / c_kms) / 2.354820045
        profile = np.exp(-0.5 * ((wavelength_nm - lam0) / sigma_nm) ** 2)
        profile /= np.trapezoid(profile[::-1], wavelength_nm[::-1])
        flux += integrated_line_flux * profile
    return Spectrum(sigma_grid_cm, flux, {"template": "emission_lines", "fwhm_kms": fwhm_kms})


def apply_redshift(spectrum: Spectrum, z: float) -> Spectrum:
    observed_wavelength = spectrum.wavelength_nm
    rest_wavelength = observed_wavelength / (1.0 + z)
    rest_flux = np.interp(
        rest_wavelength[::-1],
        observed_wavelength[::-1],
        spectrum.flux_photons_per_s_cm2_nm[::-1],
        left=0.0,
        right=0.0,
    )[::-1]
    redshifted_flux = rest_flux / (1.0 + z)
    return Spectrum(
        spectrum.sigma_cm,
        redshifted_flux,
        {**spectrum.meta, "redshift": z},
    )


def from_file(filepath: str | Path, sigma_grid_cm: np.ndarray | None = None) -> Spectrum:
    sigma_grid_cm = default_sigma_grid() if sigma_grid_cm is None else np.asarray(sigma_grid_cm, dtype=float)
    file_path = Path(filepath)
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        wavelength_nm, flux = _read_csv_spectrum(file_path)
    elif suffix in {".fits", ".fit", ".fts"}:
        wavelength_nm, flux = _read_fits_spectrum(file_path)
    else:
        raise ValueError(f"Unsupported spectrum file format: {suffix}")
    return _spectrum_from_wavelength_flux(wavelength_nm, flux, sigma_grid_cm, {"source_file": str(file_path)})


def load_template(name: str, sigma_grid_cm: np.ndarray | None = None, **kwargs: Any) -> Spectrum:
    sigma_grid_cm = default_sigma_grid() if sigma_grid_cm is None else np.asarray(sigma_grid_cm, dtype=float)
    name_key = name.lower().strip()
    if name_key == "flat":
        return Spectrum(sigma_grid_cm, np.ones_like(sigma_grid_cm), {"template": "flat"})
    if name_key == "blackbody":
        return blackbody(kwargs.get("T_eff", 6000.0), kwargs.get("mag", 18.0), kwargs.get("band", "r"), sigma_grid_cm)
    if name_key == "hii_region":
        ratios = {
            "oii_3727": 0.45,
            "hbeta": 0.30,
            "oiii_4959": 0.70,
            "oiii_5007": 2.10,
            "nii_6548": 0.18,
            "ha": 1.00,
            "nii_6583": 0.55,
            "sii_6716": 0.30,
            "sii_6731": 0.25,
        }
        total_flux = kwargs.get("line_flux", 2.0e-2)
        return emission_lines(
            {line: total_flux * ratio for line, ratio in ratios.items()},
            fwhm_kms=kwargs.get("fwhm_kms", 60.0),
            sigma_grid_cm=sigma_grid_cm,
            continuum_level=kwargs.get("continuum_level", 0.0),
        )
    if name_key == "planetary_nebula":
        return emission_lines(
            {
                "oiii_4959": 8.0e-3,
                "oiii_5007": 2.4e-2,
                "ha": 4.0e-3,
                "nii_6583": 2.0e-3,
            },
            fwhm_kms=kwargs.get("fwhm_kms", 25.0),
            sigma_grid_cm=sigma_grid_cm,
            continuum_level=kwargs.get("continuum_level", 1.0e-5),
        )

    file_name = f"{name_key}.csv"
    with resources.as_file(resources.files("mkid_ifts_sim").joinpath("data", "templates", file_name)) as template_path:
        spectrum = from_file(template_path, sigma_grid_cm)
    if "magnitude" in kwargs:
        spectrum = normalize_to_ab_magnitude(spectrum, kwargs["magnitude"], kwargs.get("band", "r"))
    return Spectrum(spectrum.sigma_cm, spectrum.flux_photons_per_s_cm2_nm, {**spectrum.meta, "template": name_key})


def make_input_source(request: Mapping[str, Any], config: InstrumentConfig | None = None) -> Spectrum:
    config = InstrumentConfig() if config is None else config
    sigma_grid_cm = config.sigma_grid()
    mode = request.get("mode", "point").lower()
    if mode == "point":
        spectral_type = request.get("spectral_type", "stellar_g2v")
        magnitude = float(request.get("magnitude", 20.0))
        band = request.get("band", "r")
        spectrum = load_template(spectral_type, sigma_grid_cm=sigma_grid_cm)
        return normalize_to_ab_magnitude(spectrum, magnitude, band)
    if mode == "extended":
        template = request.get("template", "composite_galaxy")
        spectrum = load_template(template, sigma_grid_cm=sigma_grid_cm)
        surface_brightness = float(request.get("surface_brightness", 21.0))
        band = request.get("band", "r")
        return normalize_to_ab_magnitude(spectrum, surface_brightness, band)
    if mode == "file":
        return from_file(request["filepath"], sigma_grid_cm=sigma_grid_cm)
    raise ValueError(f"Unsupported source mode: {mode}")


def _spectrum_from_wavelength_flux(
    wavelength_nm: np.ndarray,
    flux: np.ndarray,
    sigma_grid_cm: np.ndarray,
    meta: dict[str, Any] | None = None,
) -> Spectrum:
    wavelength_nm = np.asarray(wavelength_nm, dtype=float)
    flux = np.asarray(flux, dtype=float)
    order = np.argsort(wavelength_nm)
    wavelength_nm = wavelength_nm[order]
    flux = flux[order]
    wavelength_out = (1.0e7 / sigma_grid_cm)[::-1]
    flux_out = np.interp(wavelength_out, wavelength_nm, flux, left=0.0, right=0.0)[::-1]
    return Spectrum(sigma_grid_cm, flux_out, meta or {})


def _read_csv_spectrum(path: Path) -> tuple[np.ndarray, np.ndarray]:
    wavelength_nm: list[float] = []
    flux: list[float] = []
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            keys = {key.lower(): value for key, value in row.items()}
            wavelength_nm.append(float(keys["wavelength_nm"]))
            flux_value = keys.get("flux_photons_per_s_cm2_nm", keys.get("flux_relative"))
            if flux_value is None:
                raise ValueError("CSV spectrum must include flux_photons_per_s_cm2_nm or flux_relative.")
            flux.append(float(flux_value))
    return np.asarray(wavelength_nm), np.asarray(flux)


def _read_fits_spectrum(path: Path) -> tuple[np.ndarray, np.ndarray]:
    with fits.open(path) as hdul:
        table = hdul[1].data if len(hdul) > 1 else hdul[0].data
        names = {name.lower(): name for name in table.names}
        wavelength_nm = np.asarray(table[names["wavelength_nm"]], dtype=float)
        flux_key = "flux_photons_per_s_cm2_nm" if "flux_photons_per_s_cm2_nm" in names else "flux"
        flux = np.asarray(table[names[flux_key]], dtype=float)
    return wavelength_nm, flux
