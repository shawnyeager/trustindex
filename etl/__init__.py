"""ETL package for the Global Trust Index.

Modules:
- discover: find new source releases
- ingest: download and parse raw files
- transform: normalize to 0–100 and map to pillars
- assemble: build country-year rows and GTI
"""

