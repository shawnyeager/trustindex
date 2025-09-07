from typing import Optional


def rescale_wgi(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return ((value + 2.5) / 5.0) * 100.0


def oecd_0_10_to_100(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return value * 10.0


def governance_proxy(cpi_0_100: Optional[float], wgi_scaled_0_100: Optional[float]) -> Optional[float]:
    if cpi_0_100 is not None and wgi_scaled_0_100 is not None:
        return 0.5 * cpi_0_100 + 0.5 * wgi_scaled_0_100
    return cpi_0_100 or wgi_scaled_0_100


def gti(inst: Optional[float], inter: Optional[float], gov: Optional[float]) -> Optional[float]:
    # Apply proportional reweighting based on available pillars
    available = [("INST", inst), ("INTER", inter), ("GOV", gov)]
    present = {k: v for k, v in available if v is not None}
    if len(present) == 3:
        return 0.4 * inst + 0.3 * inter + 0.3 * gov  # type: ignore
    if set(present.keys()) == {"INST", "GOV"}:
        return 0.6 * inst + 0.4 * gov  # type: ignore
    if set(present.keys()) == {"INST", "INTER"}:
        return 0.57 * inst + 0.43 * inter  # type: ignore
    if set(present.keys()) == {"INTER", "GOV"}:
        return 0.5 * inter + 0.5 * gov  # type: ignore
    if len(present) == 1 and "GOV" in present:
        return gov
    return None

