#!/usr/bin/env python3
"""
Download a simplified world countries GeoJSON (Natural Earth 110m) into data/reference/world-110m.geojson.

Sources:
- https://geojson.xyz/world/ne_110m_admin_0_countries.geojson (public domain Natural Earth)
"""
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from pathlib import Path
import sys


URLS = [
    "https://geojson.xyz/world/ne_110m_admin_0_countries.geojson",
]


def download(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "GTI/0.1 (+https://example.local)"})
    with urlopen(req, timeout=30) as r:
        return r.read()


def main() -> int:
    out = Path("data/reference/world-110m.geojson")
    out.parent.mkdir(parents=True, exist_ok=True)
    last_err = None
    for u in URLS:
        try:
            print(f"Fetching {u} ...")
            data = download(u)
            out.write_bytes(data)
            print(f"Saved → {out} ({len(data)} bytes)")
            return 0
        except (URLError, HTTPError, TimeoutError) as e:
            print(f"Failed: {e}")
            last_err = e
        except Exception as e:
            print(f"Error: {e}")
            last_err = e
    print("All sources failed.")
    return 1 if last_err else 2


if __name__ == "__main__":
    sys.exit(main())

