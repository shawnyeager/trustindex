#!/usr/bin/env python3
import json
import sys
import time
from urllib.request import urlopen, Request


BASE = "http://localhost:8000"


def fetch_json(path: str):
    url = BASE + path
    with urlopen(Request(url)) as r:
        return json.loads(r.read().decode("utf-8"))


def assert_true(cond: bool, msg: str):
    if not cond:
        print(f"FAIL: {msg}")
        sys.exit(1)


def main():
    # Wait briefly for API to be up
    for _ in range(20):
        try:
            fetch_json("/api/methodology")
            break
        except Exception:
            time.sleep(0.5)

    data = fetch_json("/api/score?year=2024&trust_type=proxy")
    assert_true(isinstance(data, list) and len(data) >= 5, "score should return at least 5 rows")
    iso3s = {r["iso3"] for r in data}
    expected = {"USA", "SWE", "BRA", "NGA", "IND"}
    assert_true(expected.issubset(iso3s), "score should include expected countries")

    countries = fetch_json("/api/countries")
    assert_true(isinstance(countries, list) and len(countries) >= 5, "countries should return at least 5 rows")

    usa = fetch_json("/api/country/USA?from=2024&to=2024")
    assert_true(usa.get("iso3") == "USA", "country iso3 should be USA")
    series = usa.get("series", [])
    assert_true(len(series) == 1 and series[0]["year"] == 2024, "country series for 2024 should have one item")

    print("Smoke tests passed.")


if __name__ == "__main__":
    main()

