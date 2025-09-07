from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, Response
from fastapi import HTTPException
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import json

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


app = FastAPI(title="Global Trust Index API", version="0.1.0")


# DB pool
from . import db as dbmod  # local db helper


# In-memory placeholder data for fallback
_COUNTRIES_FALLBACK = [
    {"iso3": "USA", "name": "United States", "region": "Americas", "latest_year": 2024, "latest_gti": 62.0, "confidence_tier": "C"},
    {"iso3": "SWE", "name": "Sweden", "region": "Europe", "latest_year": 2024, "latest_gti": 75.0, "confidence_tier": "C"},
    {"iso3": "BRA", "name": "Brazil", "region": "Americas", "latest_year": 2024, "latest_gti": 48.0, "confidence_tier": "C"},
    {"iso3": "NGA", "name": "Nigeria", "region": "Africa", "latest_year": 2024, "latest_gti": 45.0, "confidence_tier": "C"},
    {"iso3": "IND", "name": "India", "region": "Asia", "latest_year": 2024, "latest_gti": 55.0, "confidence_tier": "C"},
]


@app.on_event("startup")
def _startup():
    # Initialize DB connection pool if POSTGRES_URL present
    dbmod.init_pool()


@app.on_event("shutdown")
def _shutdown():
    dbmod.close_pool()


@app.get("/api/countries")
def list_countries() -> List[Dict[str, Any]]:
    conn = dbmod.acquire_conn()
    if conn is None:
        return _COUNTRIES_FALLBACK
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                with years as (
                  select iso3, max(year) as latest_year
                    from observations
                   where trust_type in ('cpi','wgi')
                   group by iso3
                ),
                cpi as (
                  select o.iso3, o.year, o.score_0_100 as cpi
                    from observations o join years y on y.iso3 = o.iso3 and y.latest_year = o.year
                   where o.trust_type = 'cpi'
                ),
                wgi as (
                  select o.iso3, o.year, o.score_0_100 as wgi
                    from observations o join years y on y.iso3 = o.iso3 and y.latest_year = o.year
                   where o.trust_type = 'wgi'
                )
                select c.iso3, c.name, c.region,
                       y.latest_year,
                       case when cpi.cpi is not null and wgi.wgi is not null then 0.5*cpi.cpi + 0.5*wgi.wgi
                            else coalesce(cpi.cpi, wgi.wgi) end as latest_gti
                  from countries c
                  left join years y on y.iso3 = c.iso3
                  left join cpi on cpi.iso3 = c.iso3 and cpi.year = y.latest_year
                  left join wgi on wgi.iso3 = c.iso3 and wgi.year = y.latest_year
                 where y.latest_year is not null
                 order by c.name
                """
            )
            rows = cur.fetchall()
            items = []
            for iso3, name, region, latest_year, latest_gti in rows:
                if latest_year is None:
                    continue
                items.append({
                    "iso3": iso3,
                    "name": name,
                    "region": region,
                    "latest_year": int(latest_year),
                    "latest_gti": float(latest_gti) if latest_gti is not None else None,
                    "confidence_tier": "C",  # proxy-only for now
                })
            return items
    finally:
        dbmod.release_conn(conn)


@app.get("/api/score")
def score(year: int = Query(..., ge=1900, le=datetime.now().year), trust_type: str = Query("proxy")) -> List[Dict[str, Any]]:
    trust_type = trust_type.lower()
    if trust_type not in ("proxy", "core"):
        trust_type = "proxy"
    conn = dbmod.acquire_conn()
    if conn is None:
        # Fallback to in-memory demo
        results = []
        for c in _COUNTRIES_FALLBACK:
            results.append({
                "iso3": c["iso3"],
                "year": year,
                "trust_type": trust_type,
                "GTI": c.get("latest_gti", None),
                "confidence_tier": c.get("confidence_tier", "C"),
            })
        return results
    try:
        with conn.cursor() as cur:
            # Compute GOV = 0.5*CPI + 0.5*WGI when both present; else passthrough
            cur.execute(
                """
                with cpi as (
                  select iso3, score_0_100 as cpi from observations where year = %s and trust_type = 'cpi'
                ), wgi as (
                  select iso3, score_0_100 as wgi from observations where year = %s and trust_type = 'wgi'
                )
                select coalesce(cpi.iso3, wgi.iso3) as iso3,
                       %s as year,
                       case when cpi.cpi is not null and wgi.wgi is not null then 0.5*cpi.cpi + 0.5*wgi.wgi
                            else coalesce(cpi.cpi, wgi.wgi) end as gti
                  from cpi full outer join wgi on wgi.iso3 = cpi.iso3
                 order by 1
                """,
                (year, year, year),
            )
            results = []
            for iso3, y, gti in cur.fetchall():
                results.append({
                    "iso3": iso3,
                    "year": int(y),
                    "trust_type": trust_type,
                    "GTI": float(gti) if gti is not None else None,
                    "confidence_tier": "C",
                })
            return results
    finally:
        dbmod.release_conn(conn)


@app.get("/api/country/{iso3}")
def country_detail(iso3: str, from_: Optional[int] = Query(None, alias="from"), to: Optional[int] = None) -> Dict[str, Any]:
    conn = dbmod.acquire_conn()
    if conn is None:
        # Fallback based on in-memory defaults
        base = next((c for c in _COUNTRIES_FALLBACK if c["iso3"].upper() == iso3.upper()), None)
        if not base:
            return {"iso3": iso3.upper(), "series": [], "sources_used": [], "confidence": []}
        latest = base["latest_year"]
        start = from_ or (latest - 4)
        end = to or latest
        series = [{
            "year": y,
            "GTI": base["latest_gti"],
            "INTER": None,
            "INST": None,
            "GOV": base["latest_gti"],
            "confidence_tier": "C",
        } for y in range(start, end + 1)]
        return {"iso3": base["iso3"], "series": series, "sources_used": [], "confidence": [s["confidence_tier"] for s in series]}
    try:
        with conn.cursor() as cur:
            # Determine bounds if not provided
            if from_ is None or to is None:
                cur.execute(
                    """
                    select min(year), max(year)
                      from observations
                     where iso3 = %s and trust_type in ('cpi','governance')
                    """,
                    (iso3.upper(),),
                )
                miny, maxy = cur.fetchone() or (None, None)
                if miny is None:
                    return {"iso3": iso3.upper(), "series": [], "sources_used": [], "confidence": []}
                if from_ is None:
                    from_ = int(max(miny, (maxy or miny) - 4))
                if to is None:
                    to = int(maxy)

            cur.execute(
                """
                with cpi as (
                  select year, score_0_100 as cpi from observations where iso3 = %s and trust_type = 'cpi'
                ), wgi as (
                  select year, score_0_100 as wgi from observations where iso3 = %s and trust_type = 'wgi'
                )
                select y as year,
                       case when cpi.cpi is not null and wgi.wgi is not null then 0.5*cpi.cpi + 0.5*wgi.wgi
                            else coalesce(cpi.cpi, wgi.wgi) end as gti,
                       case when cpi.cpi is not null and wgi.wgi is not null then 0.5*cpi.cpi + 0.5*wgi.wgi
                            else coalesce(cpi.cpi, wgi.wgi) end as gov
                  from generate_series(%s, %s) as y
                  left join cpi on cpi.year = y
                  left join wgi on wgi.year = y
                 order by y
                """,
                (iso3.upper(), iso3.upper(), from_, to),
            )
            series = []
            for (y, gti, gov) in cur.fetchall():
                series.append({
                    "year": int(y),
                    "GTI": float(gti) if gti is not None else None,
                    "INTER": None,
                    "INST": None,
                    "GOV": float(gov) if gov is not None else (float(gti) if gti is not None else None),
                    "confidence_tier": "C",
                })
            return {
                "iso3": iso3.upper(),
                "series": series,
                "sources_used": ["CPI", "WGI"],
                "confidence": [s["confidence_tier"] for s in series],
            }
    finally:
        dbmod.release_conn(conn)


@app.get("/api/methodology")
def methodology() -> Dict[str, Any]:
    # Prefer methodology.yaml if available
    meth_path = os.path.join("data", "reference", "methodology.yaml")
    if os.path.exists(meth_path) and yaml:
        with open(meth_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    # Fallback minimal JSON if YAML is missing or PyYAML not installed
    return {
        "version": "0.1.0",
        "note": "Install pyyaml and provide data/reference/methodology.yaml for full content.",
    }


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Global Trust Index — MVP</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 2rem; }
    header { margin-bottom: 1rem; }
    code { background: #f4f4f4; padding: 0.1rem 0.3rem; border-radius: 4px; }
    .row { margin: 0.5rem 0; }
    table { border-collapse: collapse; width: 100%; max-width: 900px; }
    th, td { text-align: left; padding: 0.4rem 0.6rem; border-bottom: 1px solid #eee; }
    th { background: #fafafa; }
    input[type=number] { width: 7rem; }
    small { color: #666; }
  </style>
  <script>
    async function loadCountries() {
      const res = await fetch('/api/countries');
      const data = await res.json();
      const tbody = document.querySelector('#countries tbody');
      tbody.innerHTML = '';
      for (const r of data) {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${r.iso3}</td><td>${r.name}</td><td>${r.region || ''}</td><td>${r.latest_year || ''}</td><td>${r.latest_gti ?? ''}</td><td>${r.confidence_tier || ''}</td>`;
        tbody.appendChild(tr);
      }
      document.getElementById('countries-count').textContent = data.length;
    }
    async function loadScores(evt) {
      evt?.preventDefault();
      const year = document.getElementById('year').value;
      const trust_type = document.getElementById('trust_type').value;
      const res = await fetch(`/api/score?year=${year}&trust_type=${trust_type}`);
      const data = await res.json();
      const tbody = document.querySelector('#scores tbody');
      tbody.innerHTML = '';
      for (const r of data) {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${r.iso3}</td><td>${r.year}</td><td>${r.trust_type}</td><td>${r.GTI ?? ''}</td><td>${r.confidence_tier || ''}</td>`;
        tbody.appendChild(tr);
      }
      document.getElementById('scores-count').textContent = data.length;
    }
    async function init() {
      await loadCountries();
      await loadScores();
    }
    window.addEventListener('DOMContentLoaded', init);
  </script>
  </head>
  <body>
    <header>
      <h1>Global Trust Index — MVP</h1>
      <div class=\"row\"><small>
        API docs: <a href=\"/docs\">/docs</a> • Methodology JSON: <a href=\"/api/methodology\">/api/methodology</a>
        • Map view: <a href=\"/map\">/map</a>
      </small></div>
    </header>
    <section>
      <h2>Countries <small>(<span id=\"countries-count\">0</span>)</small></h2>
      <table id=\"countries\">
        <thead><tr><th>ISO3</th><th>Name</th><th>Region</th><th>Latest Year</th><th>Latest GTI</th><th>Tier</th></tr></thead>
        <tbody></tbody>
      </table>
    </section>
    <section class=\"row\">
      <form onsubmit=\"loadScores(event)\">
        <label>Year <input id=\"year\" type=\"number\" min=\"1990\" value=\"2024\" /></label>
        <label>Trust Type
          <select id=\"trust_type\">
            <option value=\"proxy\" selected>proxy (GOV)</option>
            <option value=\"core\">core</option>
          </select>
        </label>
        <button type=\"submit\">Load Scores</button>
      </form>
    </section>
    <section>
      <h2>Scores <small>(<span id=\"scores-count\">0</span>)</small></h2>
      <table id=\"scores\">
        <thead><tr><th>ISO3</th><th>Year</th><th>Type</th><th>GTI</th><th>Tier</th></tr></thead>
        <tbody></tbody>
      </table>
    </section>
  </body>
  </html>
  """


@app.get("/map", response_class=HTMLResponse)
def map_view() -> str:
    return """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>GTI Map — MVP</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; }
    header { padding: 1rem 1.2rem; border-bottom: 1px solid #eee; }
    main { padding: 1rem 1.2rem; }
    #map { width: 100%; height: 70vh; border: 1px solid #eee; position: relative; background: #f9fbfd; }
    .controls { display: flex; gap: 1rem; align-items: center; flex-wrap: wrap; margin-bottom: 0.6rem; }
    label { display: inline-flex; align-items: center; gap: 0.4rem; }
    .legend { display: flex; gap: 0.6rem; align-items: center; margin-top: 0.4rem; }
    .swatch { width: 16px; height: 16px; display: inline-block; border-radius: 50%; border: 1px solid #ccc; }
    .tooltip { position: absolute; pointer-events: none; background: #fff; border: 1px solid #ccc; padding: 6px 8px; font-size: 12px; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.15); }
  </style>
  <script>
    // Minimal equirectangular projection (lon, lat in degrees)
    function projectLonLat(lon, lat, width, height) {
      const x = (lon + 180) / 360 * width;
      const y = (90 - lat) / 180 * height;
      return [x, y];
    }

    // Approximate country centroids (subset for MVP)
    const CENTROIDS = {
      USA: [38.0, -97.0],
      SWE: [62.0, 16.0],
      BRA: [-10.0, -55.0],
      NGA: [9.0, 8.0],
      IND: [22.0, 78.0],
    };

    // Color scale (colorblind-friendly-ish): purple -> teal -> green
    function colorFor(value) {
      if (value == null || isNaN(value)) return '#cccccc';
      const v = Math.max(0, Math.min(100, value));
      if (v < 40) return '#8e0152';
      if (v < 50) return '#c51b7d';
      if (v < 60) return '#de77ae';
      if (v < 70) return '#80cdc1';
      return '#35978f';
    }

    function renderLegend() {
      const legend = document.getElementById('legend');
      const bins = [
        {label: '< 40', color: '#8e0152'},
        {label: '40–50', color: '#c51b7d'},
        {label: '50–60', color: '#de77ae'},
        {label: '60–70', color: '#80cdc1'},
        {label: '≥ 70', color: '#35978f'},
      ];
      legend.innerHTML = '';
      for (const b of bins) {
        const item = document.createElement('div');
        item.innerHTML = `<span class=\"swatch\" style=\"background:${b.color}\"></span> ${b.label}`;
        legend.appendChild(item);
      }
    }

    async function getWorldGeoJSON() {
      const urls = [
        '/assets/world-110m.geojson',
        'https://geojson.xyz/world/ne_110m_admin_0_countries.geojson',
        '/assets/world.geojson'
      ];
      for (const u of urls) {
        try {
          const res = await fetch(u, { cache: 'force-cache' });
          if (res.ok) return await res.json();
        } catch (e) { /* try next */ }
      }
      return { type: 'FeatureCollection', features: [] };
    }

    async function loadScores(evt) {
      evt?.preventDefault();
      const year = document.getElementById('year').value;
      const trust_type = document.getElementById('trust_type').value;
      const res = await fetch(`/api/score?year=${year}&trust_type=${trust_type}`);
      const data = await res.json();
      const gj = await getWorldGeoJSON();
      drawMapChoropleth(gj, data);
    }

    function drawPathFromRings(rings, width, height) {
      // rings: array of arrays of [lon,lat]
      const cmds = [];
      for (const ring of rings) {
        for (let i = 0; i < ring.length; i++) {
          const [lon, lat] = ring[i];
          const [x, y] = projectLonLat(lon, lat, width, height);
          cmds.push((i === 0 ? 'M' : 'L') + x.toFixed(2) + ' ' + y.toFixed(2));
        }
        cmds.push('Z');
      }
      return cmds.join(' ');
    }

    function drawMapChoropleth(geojson, scores) {
      const map = document.getElementById('map');
      const rect = map.getBoundingClientRect();
      const width = rect.width, height = rect.height;
      map.innerHTML = '';
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('width', width);
      svg.setAttribute('height', height);
      svg.style.display = 'block';
      map.appendChild(svg);

      const tooltip = document.createElement('div');
      tooltip.className = 'tooltip';
      tooltip.style.display = 'none';
      map.appendChild(tooltip);

      const byIso = Object.create(null);
      for (const s of scores) byIso[s.iso3] = s;

      let count = 0;
      for (const f of geojson.features || []) {
        const iso3 = (f.properties && (f.properties.iso3 || f.properties.ISO_A3 || f.properties.iso_a3)) || '';
        const name = (f.properties && (f.properties.name || f.properties.ADMIN || f.properties.admin)) || iso3;
        const score = byIso[iso3]?.GTI ?? null;
        const fill = colorFor(score);
        const geom = f.geometry || {};
        if (!geom.type) continue;
        const addPath = (rings) => {
          const pathStr = drawPathFromRings(rings, width, height);
          const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
          path.setAttribute('d', pathStr);
          path.setAttribute('fill', fill);
          path.setAttribute('stroke', '#333');
          path.setAttribute('stroke-width', '0.5');
          path.style.cursor = 'pointer';
          path.addEventListener('mousemove', (e) => {
            tooltip.style.left = (e.offsetX + 10) + 'px';
            tooltip.style.top = (e.offsetY + 10) + 'px';
            tooltip.style.display = 'block';
            tooltip.innerHTML = `<strong>${name} (${iso3})</strong><br/>GTI: ${score ?? 'n/a'}`;
          });
          path.addEventListener('mouseleave', () => {
            tooltip.style.display = 'none';
          });
          svg.appendChild(path);
          count++;
        };
        if (geom.type === 'Polygon') {
          addPath(geom.coordinates);
        } else if (geom.type === 'MultiPolygon') {
          for (const rings of geom.coordinates) addPath(rings);
        }
      }
      document.getElementById('rendered-count').textContent = count;
    }

    async function init() {
      renderLegend();
      await loadScores();
      window.addEventListener('resize', () => loadScores());
    }
    window.addEventListener('DOMContentLoaded', init);
  </script>
</head>
<body>
  <header>
    <strong>Global Trust Index — Map (MVP)</strong>
    <div><small><a href=\"/\">Home</a> • <a href=\"/docs\">API docs</a> • Basemap: <a href=\"https://www.naturalearthdata.com/\" target=\"_blank\" rel=\"noopener\">Natural Earth</a></small></div>
  </header>
  <main>
    <form class=\"controls\" onsubmit=\"loadScores(event)\">
      <label>Year <input id=\"year\" type=\"number\" min=\"1990\" value=\"2024\" /></label>
      <label>Trust Type
        <select id=\"trust_type\">
          <option value=\"proxy\" selected>proxy (GOV)</option>
          <option value=\"core\">core</option>
        </select>
      </label>
      <button type=\"submit\">Render</button>
      <span><small>Rendered: <span id=\"rendered-count\">0</span></small></span>
    </form>
    <div id=\"map\"></div>
    <div class=\"legend\" id=\"legend\"></div>
  </main>
</body>
</html>
"""


@app.get("/assets/world.geojson")
def world_geojson() -> Response:
    path = os.path.join("data", "reference", "world_5.geojson")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="world_5.geojson not found")
    with open(path, "rb") as f:
        data = f.read()
    return Response(content=data, media_type="application/geo+json")


@app.get("/assets/world-110m.geojson")
def world_110m_geojson() -> Response:
    path = os.path.join("data", "reference", "world-110m.geojson")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="world-110m.geojson not found")
    with open(path, "rb") as f:
        data = f.read()
    return Response(content=data, media_type="application/geo+json")
