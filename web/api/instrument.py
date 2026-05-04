from __future__ import annotations

from mkid_ifts_sim import InstrumentConfig
from web.api.schemas import InstrumentPayload


def merge_instrument(payload: InstrumentPayload) -> InstrumentConfig:
    """Apply optional overrides onto package defaults."""
    base = InstrumentConfig()
    data = base.to_dict()
    for key, value in payload.model_dump(exclude_none=True).items():
        data[key] = value
    return InstrumentConfig.from_mapping(data)
