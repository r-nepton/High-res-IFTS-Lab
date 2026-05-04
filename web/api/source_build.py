from __future__ import annotations

from mkid_ifts_sim import InstrumentConfig, Spectrum, make_input_source, load_template
from web.api.schemas import SourcePayload


def build_spectrum(source: SourcePayload, config: InstrumentConfig) -> Spectrum:
    """Build a source spectrum; avoid file mode. Supports line_flux for emission templates."""
    if source.mode == "point":
        grid = config.sigma_grid()
        st = source.spectral_type.lower()
        if st == "hii_region":
            lf = 2.0e-2 if source.line_flux is None else float(source.line_flux)
            return load_template("hii_region", sigma_grid_cm=grid, line_flux=lf)
        if st == "planetary_nebula":
            return load_template("planetary_nebula", sigma_grid_cm=grid)
        request: dict = {
            "mode": "point",
            "spectral_type": source.spectral_type,
            "magnitude": source.magnitude,
            "band": source.band,
        }
        return make_input_source(request, config)
    request = {
        "mode": "extended",
        "template": source.template,
        "surface_brightness": source.surface_brightness,
        "band": source.band,
    }
    return make_input_source(request, config)
