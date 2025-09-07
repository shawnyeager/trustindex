# AGENTS.md — Global Trust Index (Open Data)

> Owner: Trust Index project  
> Status: Draft v0.1  
> Scope: Agent workflows for data ingestion, normalization, and API/UI support of the Global Trust Index (GTI) built from programmatically accessible sources.

---

## 1) Mission & Constraints

**Mission:** Produce a credible, transparent, and updateable Global Trust Index (GTI) and country-level detail views using *only* open or programmatically accessible data sources.

**Out of Scope:** Proprietary sources requiring paid licenses (e.g., Gallup World Poll) and datasets without redistribution rights (e.g., full Edelman microdata). Where helpful, we may surface links or metadata but do not store restricted raw values.

**Quality Values:** Transparency, reproducibility, provenance, cautious interpolation, clear confidence flags.

---

## 2) Data Sources & Access Modes

> Agents must only use sources with documented public access (API or bulk download) and record access method per source.

### Core Surveys & Indices
- **World Values Survey (WVS):** bulk CSV/SPSS by wave (free registration).
- **European Social Survey (ESS):** programmatic access via NSD/ESS endpoints; bulk downloads.
- **Regional Barometers:** Afrobarometer, Arab Barometer, Latinobarómetro, Asian Barometer — bulk CSV/SPSS; terms-of-use apply.
- **OECD Trust Survey/Indicators:** API via OECD.Stat (JSON/CSV).
- **Transparency International CPI:** annual CSV/Excel (open).
- **World Bank Worldwide Governance Indicators (WGI):** API + bulk CSV/Excel (open).
- **Pew Global Attitudes:** downloadable CSV/SPSS (topic/year), no live API.

### Prohibited/Conditional
- **Gallup World Poll:** proprietary; do not store/use unless explicit license is obtained (then handled via separate sealed pipeline).
- **Edelman Trust Barometer:** public PDFs/infographics; avoid scraping numbers without permission; may store metadata/links.

---

## 3) Conceptual Model

GTI blends three pillars:
1. **Interpersonal Trust** — % agreeing *“Most people can be trusted.”* (WVS/ESS/Regional)
2. **Institutional Trust** — % expressing confidence in national government (or closest comparable measure) (WVS/ESS/Regional/OECD)
3. **Governance/Integrity Proxy** — institutional quality/corruption measures (TI CPI, WGI Rule of Law & Government Effectiveness)

All inputs are normalized to a 0–100 scale. GTI is computed per country-year with data provenance and confidence flags.

---

## 4) Normalization Rules (0–100)

- **Percent-based survey items** (e.g., WVS trust-in-people): `score = raw_percent` (0–100).
- **OECD/ESS institutional trust** (if percentage or 0–10 scale):
  - If 0–10: `score = raw * 10`.
  - If categorical, map to % trusting per instrument’s codebook.
- **TI CPI** (0–100, where higher = *less* corruption): use directly as a *positive* governance signal.
- **WGI** (−2.5…+2.5): rescale via `((raw + 2.5) / 5) * 100` for each selected dimension; if using both Rule of Law and Government Effectiveness, average them.

**Governance Proxy (GOV):** If both CPI and WGI available: `GOV = 0.5 * CPI + 0.5 * WGI_avg`.

---

## 5) GTI Aggregation & Weighting

Let `INST` = Institutional Trust (0–100), `INTER` = Interpersonal Trust (0–100), `GOV` = Governance Proxy (0–100).

**Primary blend (all three present):**
```
GTI = 0.4 * INST + 0.3 * INTER + 0.3 * GOV
```

**Two-pillar availability:** reweight proportionally:
- INST + GOV → `GTI = 0.6 * INST + 0.4 * GOV`
- INST + INTER → `GTI = 0.57 * INST + 0.43 * INTER` (proportional to 0.4/0.3)
- INTER + GOV → `GTI = 0.5 * INTER + 0.5 * GOV`

**Proxy-only:** if only GOV exists → `GTI = GOV` and confidence flag = `C`.

---

## 6) Time Handling & Confidence Decay

- **Survey waves:** assign to observed year. For intervening years, carry last value forward up to 3 years with no penalty. Beyond 3 years, apply confidence decay to the *pillar* (not the value) at −3% per elapsed year for the confidence metric only.
- **Annual indices (CPI, WGI, OECD where applicable):** use directly; no decay while current.

**Confidence tiers per country-year:**
- `A` = At least one *current* interpersonal or institutional survey value (≤3y old) **and** current governance proxy.
- `B` = Survey value older than 3y *or* only one survey pillar present, plus governance proxy.
- `C` = Governance proxy only (no valid survey items within 7y).

Store `confidence_score` (0–1) computed from recency and completeness; display tier alongside numeric score.

---

## 7) Data Schema (Postgres)

**countries**
- `iso3` (pk), `iso2`, `name`, `region`, `income_group`, `geom` (PostGIS)

**observations**
- `id` (pk), `iso3`, `year`, `source`, `trust_type` (`interpersonal|institutional|governance|wgi|cpi|oecd|derived`),
- `raw_value`, `raw_unit`, `score_0_100`, `sample_n`, `method_notes`, `source_url`, `ingested_at`

**country_year** (materialized view)
- `iso3`, `year`, `INTER`, `INST`, `GOV`, `GTI`, `confidence_score`, `confidence_tier`, `sources_used` (jsonb), `version`

**source_metadata**
- `source`, `description`, `cadence`, `coverage`, `license`, `access_mode`, `weighting_notes`

Indexes: `(iso3, year)`, `(trust_type, year)`, GIN on `sources_used`.

---

## 8) API Contract (for UI & external users)

- `GET /api/countries` → `[ { iso3, name, region, latest_year, latest_gti, confidence_tier } ]`
- `GET /api/score?year=YYYY&trust_type=core` → per-country GTI and tier for the specified year.
- `GET /api/country/{iso3}?from=YYYY&to=YYYY` → { series: GTI, pillars, sources_used[], confidence[] }.
- `GET /api/methodology` → current normalization/weights (versioned JSON/YAML).

**Headers/Caching:** `s-maxage=86400, stale-while-revalidate=604800`. Version all responses with `X-GTI-Version`.

---

## 9) ETL Agent Responsibilities

**ETL::Discover**
- Poll source endpoints/pages for new releases (CPI, WGI annually; ESS/OECD per release; WVS/barometers per wave).
- Emit events to the ingest queue with `source`, `release_id`, `url`, `license`.

**ETL::Ingest**
- Download CSV/Excel/SPSS; log checksum + license text.
- Parse country names → ISO3 using a controlled mapping (store exceptions).
- Validate schema; coerce scales to canonical units.

**ETL::Transform**
- Normalize to 0–100 per rules (Section 4).
- Map variables to `interpersonal` / `institutional` categories using source-specific codebooks.
- Compute per-country pillar values and governance proxy.

**ETL::Assemble**
- Build `country_year` rows; compute GTI per weights (Section 5).
- Compute confidence tier/score (Section 6).
- Upsert into DB; refresh materialized views.

**ETL::Publish**
- Trigger tile rebuild for new years (tippecanoe → MVT) and purge CDN cache.
- Post release notes with source versions and diffs (see Section 12).

---

## 10) Frontend Agent Responsibilities

- Render choropleth via vector tiles (`trust_core_{year}.mvt`).
- Provide filter modes: Core (GTI), Interpersonal, Institutional, CPI, WGI.
- Country panel shows latest values with provenance (source + year + link) and confidence tier.
- Comparison drawer for up to 4 countries.
- Accessibility: keyboard selection of countries, colorblind-safe palettes, high-contrast toggle.

---

## 11) QA & Data Ethics

- **Outlier checks:** flag year-over-year changes > 25 points for human review.
- **Provenance:** every displayed value must show source + year in tooltips.
- **Licensing:** store and expose license strings; block export if license forbids redistribution.
- **Transparency:** publish methodology JSON used to compute each GTI release.

---

## 12) Releases & Versioning

- Semantic versioning for methodology and data:
  - **Major**: changes to pillars/weights/scales.
  - **Minor**: source additions, mapping updates, country boundary adjustments.
  - **Patch**: bugfixes, data corrections.
- Create a signed **Release Note** per data drop: sources, versions, counts, known gaps.

---

## 13) Examples

**Example: Governance proxy (CPI & WGI)**
- CPI 62, WGI avg 0.8 → WGI_scaled = ((0.8 + 2.5) / 5) * 100 = 66.0  
  GOV = 0.5 * 62 + 0.5 * 66 = **64.0**

**Example: GTI with all pillars**
- INST=68, INTER=52, GOV=64 → GTI = 0.4*68 + 0.3*52 + 0.3*64 = **61.8**

**Confidence tiering (illustrative)**
- Last interpersonal survey 2y old → no decay, Tier `A` if INST also ≤3y and GOV current.
- If surveys are >5y old → Tier `B`; proxy-only → `C`.

---

## 14) Agent Prompts (Codex)

**ETL::Discover (daily)**
- *“Check for new releases from TI CPI, WGI, OECD, ESS, WVS, Afrobarometer, Arab Barometer, Latinobarómetro, Asian Barometer. For each, if a new file or release ID exists, enqueue an ingest job with source, year, URL, and license.”*

**ETL::Ingest (per job)**
- *“Download the provided file. Validate against the source schema. Map countries to ISO3. Emit normalized observations with trust_type and score_0_100. Log provenance and checksums.”*

**ETL::Assemble (nightly)**
- *“For each country-year, compute INTER, INST, GOV, GTI as defined; compute confidence tier; upsert into `country_year`; refresh MVs; trigger tile rebuilds for updated years.”*

**Frontend::Publish (on change)**
- *“Invalidate CDN for /tiles and /api/score for affected years; post a release note summarizing changes.”*

---

## 15) Security & Compliance

- Store least-privilege credentials for APIs (OECD, WGI) in a secrets manager.
- Respect robots.txt and terms-of-use; avoid scraping sites without explicit permission.
- Provide a data removal path for sources that change their licenses.

---

## 16) Roadmap

1. **MVP**: GTI latest-year map, country panel, methodology page.  
2. **V1.1**: Time slider + trendlines; CPI/WGI overlays.  
3. **V1.2**: ESS & regional barometer toggles; comparison mode.  
4. **V1.3**: Download center (CSV/PNG) with license-aware gating.  
5. **V2.0**: Narrative “Story mode”; per-country briefs; API keys for partners.

---

## 17) Glossary

- **GTI**: Global Trust Index (0–100).  
- **INTER**: Interpersonal trust pillar.  
- **INST**: Institutional trust pillar.  
- **GOV**: Governance proxy pillar (CPI + WGI).  
- **Confidence Tier**: A/B/C data completeness/recency quality band.  

---

**End of AGENTS.md**
