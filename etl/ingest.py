from dataclasses import dataclass
from typing import Optional, Dict, Any
import hashlib


@dataclass
class RawFile:
    source: str
    url: str
    content: bytes
    checksum: str
    license: str


def download_stub(source: str, url: str, license: str) -> RawFile:
    # No network in this environment; create a deterministic dummy payload
    payload = f"{source},{url},{license}".encode("utf-8")
    checksum = hashlib.sha256(payload).hexdigest()
    return RawFile(source=source, url=url, content=payload, checksum=checksum, license=license)


def parse_stub(raw: RawFile) -> Dict[str, Any]:
    # Return a minimal schema preview
    return {
        "source": raw.source,
        "records": 0,
        "checksum": raw.checksum,
        "notes": "Parser not implemented in init stub.",
    }


if __name__ == "__main__":
    rf = download_stub("TI_CPI", "https://example.org/cpi_2023.csv", "CC BY 4.0")
    print(parse_stub(rf))

