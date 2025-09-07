from dataclasses import dataclass
from typing import Dict, Any, Optional
from .transform import gti


@dataclass
class Pillars:
    INTER: Optional[float]
    INST: Optional[float]
    GOV: Optional[float]


def compute_country_year(iso3: str, year: int, pillars: Pillars) -> Dict[str, Any]:
    score = gti(pillars.INST, pillars.INTER, pillars.GOV)
    # Confidence is not computed in init; stubbed tier selection
    tier = "A" if all(v is not None for v in [pillars.INST, pillars.INTER, pillars.GOV]) else ("B" if pillars.GOV is not None else "C")
    return {
        "iso3": iso3,
        "year": year,
        "INTER": pillars.INTER,
        "INST": pillars.INST,
        "GOV": pillars.GOV,
        "GTI": score,
        "confidence_tier": tier,
        "sources_used": {},
    }

