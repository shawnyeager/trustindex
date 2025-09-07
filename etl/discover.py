from dataclasses import dataclass
from typing import List


@dataclass
class ReleaseEvent:
    source: str
    release_id: str
    url: str
    license: str


def check_sources() -> List[ReleaseEvent]:
    # Placeholder: no network; return illustrative events
    return [
        ReleaseEvent(source="TI_CPI", release_id="2023", url="https://example.org/cpi_2023.csv", license="CC BY 4.0"),
        ReleaseEvent(source="WGI", release_id="2023", url="https://example.org/wgi_2023.csv", license="World Bank Terms"),
    ]


if __name__ == "__main__":
    for ev in check_sources():
        print(ev)

