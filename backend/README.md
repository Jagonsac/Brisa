# Brisa API and operations

FastAPI services for cycling routes, geocoding, map safety, neighborhood cyclability, BiciMAD legs, and optional AI explanations. Start with the [project README](../README.md), [architecture](../docs/architecture.md), and [routing model](../docs/routing-model.md).

## Prerequisites and startup

Use Python **3.11+**; the pinned NetworkX 3.5 dependency excludes Python 3.10. GIS dependencies need compatible wheels or native geospatial libraries. The documentation checks used Python 3.12. Network access is needed for OSM/Overpass, Nominatim, and municipal/EMT inputs; API credentials are not required for deterministic routing.

From the repository root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`. Interactive API documentation is at [http://localhost:8000/docs](http://localhost:8000/docs).

## Configuration

The backend reads process variables using `os.getenv`; it does **not** automatically load a `.env` file. Export variables in the shell, configure them in your hosting service, or use Uvicorn's explicit `--env-file` option after installing its dotenv support. `backend/.env.example` is a reference, not an automatically active configuration. It specifies `OSMNX_NETWORK_TYPE=bike`, whereas the code default is `all`; select deliberately and rebuild graphs when changing it.

| Variable | Default / purpose |
| --- | --- |
| `BRISA_ENV` | `development` |
| `FRONTEND_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173`; comma-separated CORS origins |
| `OSMNX_PLACE_QUERY` | `Madrid, Spain` |
| `OSMNX_NETWORK_TYPE` | `all` before Brisa's cycling-access filter |
| `OSMNX_GRAPH_FILENAME` | `madrid_bike.graphml` |
| `NOMINATIM_BASE_URL` | `https://nominatim.openstreetmap.org/search` |
| `NOMINATIM_USER_AGENT` | Development identifier; use a real application/contact identifier for hosted operation |
| `NOMINATIM_COUNTRY_CODES` | `es` |
| `PRECOMPUTE_CACHE_ON_STARTUP` | `true`; prepare graphs and caches in FastAPI lifespan |
| `FORCE_REBUILD_CACHE_ON_STARTUP` | `false`; rebuild derived caches during warmup |
| `RELEASE_ROUTING_MEMORY_AFTER_REQUEST` | `true`; release graph/edge/cyclability runtime caches after route requests |
| `TRIM_MEMORY_AFTER_ROUTE` | `true`; best-effort glibc memory trimming |
| `ROUTING_CACHE_VERSION` | `v2`; suffix for edge metrics and routing metadata |
| `OPENAI_API_KEY` | Empty; optional server-side secret |
| `OPENAI_ROUTE_INSIGHTS_MODEL` | Code default `gpt-5.4-mini`; choose a model available to your account |
| `OPENAI_ROUTE_INSIGHTS_TIMEOUT_SECONDS` | `12` |
| `AI_ROUTE_INSIGHTS_RATE_LIMIT` / `AI_ROUTE_INSIGHTS_WINDOW_SECONDS` | `20` requests per `300` seconds, per IP, within one process |

See [routing configuration](../docs/routing-model.md#6-profile-costs-and-configuration) for multipliers, [data configuration](../docs/data-sources.md) for source URLs, and `app/core/safety_config.py` / `cyclability_config.py` for all scoring controls. The station status URL/TTL settings remain in code, but the active multimodal planner does not consume live status.

Keep credentials out of source control, screenshots, logs, and `VITE_*` variables. The frontend's Vite variables are public build-time values; only `VITE_API_BASE_URL` is needed to point it at this API.

## Preprocessing and cache refresh

From `backend/`, with the virtual environment active:

```bash
python -m app.pipelines.build_routing_cache
python -m app.pipelines.build_safety_cache
python -m app.pipelines.build_neighborhood_cyclability
```

The first command rebuilds edge metrics and routing metadata; it loads/reuses the graph. The second builds the grid and neighborhood safety layer. The third rebuilds neighborhood cyclability, consuming edge metrics and the BiciMAD location snapshot. Check source record counts in routing metadata before treating a successful build as a complete-data build.

Startup warmup also ensures a walking graph for BiciMAD. The three pipeline commands do not write the bootstrap state file, so a later default startup may repeat work when its fingerprint is absent. `PRECOMPUTE_CACHE_ON_STARTUP=false` prevents startup warmup but allows on-demand builds.

Artifacts are described in the [cache table](../docs/architecture.md#preprocessing-and-cache-lifecycle). They are not shipped as a complete ready-to-run city dataset. Expect substantial downloads, disk use, and peak memory on a clean machine; no runtime or memory benchmark is claimed.

After changing source/scoring settings, stop API processes, preserve any valuable cached data, rebuild edge metrics first, then safety/cyclability as applicable, and restart. For a graph/network/tag-filter change, use a fresh graph filename **and ensure the separate `madrid_walk.graphml` cache is appropriate**, or archive the relevant existing graphs before regeneration. `FORCE_REBUILD_CACHE_ON_STARTUP=true` does not itself force a fresh upstream graph download. The fingerprint does not hash every configuration value, and caches do not have a universal automatic expiry.

## API reference

| Method and endpoint | Purpose |
| --- | --- |
| `GET /health` | API liveness; not full data/routing readiness |
| `GET /api/stations?source=auto` | Normalized locations; `auto`, `remote`, or `snapshot` |
| `GET /api/geocoding/suggest?q=...` | Address suggestions |
| `POST /api/routes` | One profile per request; optional `useBicimad` |
| `GET /api/safety/grid?aggregation=neighborhood` | Neighborhood layer; `aggregation=cell` for grid; optional `bbox=minLon,minLat,maxLon,maxLat` |
| `GET /api/safety/summary` | Metadata and aggregate scores |
| `GET /api/cyclability/neighborhoods` | Ranking and components |
| `GET /api/cyclability/neighborhoods/geojson` | Map layer |
| `GET /api/cyclability/neighborhoods/compare?left=001&right=002` | Comparison; replace IDs with returned neighborhood IDs |
| `GET /api/cyclability/neighborhoods/{id}` | Neighborhood detail |
| `GET /api/cyclability/neighborhoods/{id}/score-breakdown` | Component contributions, adjustments, and data gaps |
| `POST /api/ai/route-insights` | Optional interpretation of supplied summaries |

Example request (illustrative coordinates, not a stored benchmark):

```bash
curl -X POST http://localhost:8000/api/routes \
  -H 'Content-Type: application/json' \
  -d '{"origin":{"query":"Puerta del Sol","lat":40.4168,"lon":-3.7038},"destination":{"query":"Atocha","lat":40.4066,"lon":-3.6908},"mode":"balanced","useBicimad":false}'
```

See [contracts](../docs/contracts/README.md) for payload shapes. Routes return one GeoJSON feature plus summary, explanations, hazards, and provenance flags. Many errors use `detail.code` and `detail.message`; precise status handling lives in the routers.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| API startup is slow or appears blocked | Default warmup runs before serving. Inspect download/precompute logs and graph/cache files. Do not assume `/health` or startup skipping prepares data. |
| Routing fails after the API starts | Verify Overpass access, complete graph/edge caches, geocoding, and auxiliary incident/neighborhood dependencies. Try explicit coordinates to isolate geocoding. |
| CORS or connection error | Set the frontend's `VITE_API_BASE_URL=http://localhost:8000`; restart Vite after changes. Include its exact origin in `FRONTEND_ORIGINS`. |
| Zero source records or unexpectedly uniform scores | Inspect CSV coordinate/value columns, direct resource URLs, and cached raw data. Several defaults are catalog pages, not CSV resources. |
| Score unchanged after a weight change | Restart for new environment values; rebuild precomputed signals and downstream indexes when required. |
| High memory / repeated graph loading | The default release policy lowers retained memory but reloads data on later requests. Measure before disabling it; keep adequate memory for peak preprocessing. |
| Basemap says `API KEY REQUIRED` | Tile-provider access is independent of the API. The former unkeyed CARTO layer was fixed in PR #97; use the OpenStreetMap default or configure a valid CARTO key and rebuild. See [map tiles](../docs/map-tiles.md). |
| AI endpoint returns 503 or 502 | Check server-side configuration, provider access/model, timeout, and response shape. Routes remain independent of AI. |
| Tests fail | Review the four recorded upstream failures in [verification](../docs/verification.md); do not interpret them as missing GIS downloads. |

## Hosting on Railway

These are deployment instructions, not a claim that a particular backend URL is currently verified.

1. Use `backend` as the service root and install `requirements.txt` with Python 3.11+.
2. Persist the generated data directory. With the usual `/app` service root, mount a volume at `/app/data`; confirm the actual working path in your container.
3. Set `BRISA_ENV=production`, the exact frontend CORS origin, a suitable Nominatim user agent, and any source overrides. Configure optional AI secrets only on the server.
4. Start with `uvicorn app.main:app --host 0.0.0.0 --port "$PORT"`.
5. Build/precompute during a controlled run with enough memory, or supply verified precomputed artifacts. Startup rebuilding can exceed a small service's resources.
6. If using `PRECOMPUTE_CACHE_ON_STARTUP=false`, verify caches and a representative route before considering deployment ready. Missing caches can still trigger expensive work on demand.
7. Check health, map layers, a coordinate-based route, and a BiciMAD route; then restart the service and verify cache persistence.
8. For deliberate model/data refresh, use the rebuild workflow above. Restore `FORCE_REBUILD_CACHE_ON_STARTUP=false` afterwards.

`backend/app/data/bicimad_stations_snapshot.json` is outside the main data volume. Persisting only `/app/data` will not preserve updates to that snapshot across deploys. Configure the frontend API base at build time in Vercel and check map-tile provider access separately.

## Testing

```bash
python -m pip install pytest pytest-asyncio
PRECOMPUTE_CACHE_ON_STARTUP=false python -m pytest -q
```

The suite relies mostly on fixtures/stubs; no live city-wide GIS or AI-provider calls are needed for the recorded run. See [verification](../docs/verification.md) for exact results and [known issues](../docs/known-issues.md) for implementation findings.
