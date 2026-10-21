# Known implementation issues

Findings from the documentation audit of upstream commit `1523018f2500b709cca61cb9dd789d70877a8cc8`. These are implementation/test issues, not changes to the routing model in the documentation pull request. The separately authorized basemap fix is tracked in PR #97.

## Basemap access

The hosted frontend requested CARTO raster tiles without a key. CARTO returns image tiles with an embedded `API KEY REQUIRED` notice, even with HTTP 200. This was resolved in PR #97, merged and verified in production: key-free OpenStreetMap tiles are now the default, with optional CARTO basemap-key support. See [map tiles](map-tiles.md). This changes only the visual background.

## OSM bicycle tags need explicit retention

The pinned OSMnx 2.0.6 default `useful_tags_way` retains road class, lanes, speed, and access, but not `bicycle`, `cycleway`, sided cycleway tags, `segregated`, or `motorroad`. `GraphService` does not extend that list. Fresh builds can therefore omit attributes that the access filter and infrastructure scorer inspect; `highway=cycleway` remains available. Existing externally enriched GraphML caches may differ.

This was checked against the installed pinned package settings as well as the graph code. A future implementation fix should explicitly retain needed tags, invalidate/rebuild graphs and metrics, and test a representative set of legal/access cases. The documentation describes how supplied attributes are treated, not a guarantee that every cached graph contains them.

## Data ingestion can silently lose signals

[`edge_safety_service.py`](../backend/app/services/edge_safety_service.py), `_download_csv_rows`, `_load_point_csv`, and `_load_sources`:

- `IMD_CSV_URL`, `CROSSINGS_CSV_URL`, and `BIKE_CROSSINGS_CSV_URL` default to HTML catalog pages. The loader expects CSV fields; these pages returned `text/html` during the audit.
- The separate grid monthly traffic API default returned HTTP 404 during the audit; its fallback status should be checked.
- Failed requests without a cached raw file return an empty source. Unrecognized coordinate columns skip rows. A completed cache build therefore does not prove complete input coverage.
- Crossing point values are taken from `id`/`codigo`. Identifiers are not physical intensity measurements and can saturate the normalized signal.
- Incident rows are not deduplicated in the edge pipeline, although the separate grid incident loader groups by incident ID.

Next step: validate direct resources and schemas, use unit weights for point inventories where appropriate, and expose missing-source confidence/provenance in outputs. These issues were not fixed by changing the documentation.

## BiciMAD selection and explanation disagree

[`route_service.py`](../backend/app/services/route_service.py), `_pick_station_candidates`, `_evaluate_station_pairs`, `_station_payload`, and `_build_bicimad_route`:

- The active search selects one nearest candidate per endpoint within 2.2 km and evaluates at most one pair. It can fail when that pair is identical or infeasible despite other stations being usable.
- Live status is not consulted. Availability fields are null and `liveStatusUsed=false`; `isOperational=true` is a constant, not a measured status.
- Existing Spanish explanations claim to consider available bicycles and docking spaces. Those strings overstate the implementation.
- `test_branch_and_bound_prunes_pairs` expects a larger search space than the current constants permit.

Next step: correct the text immediately in a focused behavior PR, then restore availability-aware multi-candidate selection with deterministic fallbacks.

## Model interpretation and summary caveats

[`route_service.py`](../backend/app/services/route_service.py), `_compute_path`, `_build_explanations`, `_distance_to_route_meters`:

- Route summary scores are means per edge, while costs are length-weighted. Splitting a street differently can change summary labels without the same change to the objective.
- Hazard matching uses proximity to route vertices, not distance to every polyline segment.
- The `fastest` explanation refers to time/distance, but its objective is distance with a small hostility penalty. The frontend assigns durations using fixed profile speeds.
- Cycling-access rules in [`bike_legality_service.py`](../backend/app/services/bike_legality_service.py) cover selected OSM tags; they do not fully implement private/conditional/turn/directional restrictions.

Next step: align terminology, test geometry matching, and specify desired aggregation/access semantics before changing the model.

## Neighborhood normalization and overrides

[`cyclability_service.py`](../backend/app/services/cyclability_service.py), `_percentile`, `_normalize_component`, `_served_area_ratio`, `_compute_park_rebalancing`:

- Discrete floor-index percentiles can give identical lower/upper bounds on very small samples, yielding neutral 50 scores. This explains the two-row green-network fixture failure.
- The served-area proxy floors at 0.15; both examples in the failing test hit that floor.
- Casa de Campo and Los Jerónimos receive a named minimum of at least 72. This branch runs before the general rebalancing-enabled check, so disabling general park rebalancing does not disable those named overrides.
- Standard debug component contributions can sum to a different value than the adjusted total. The response includes `rebalancing` and must be interpreted with it.
- `dataQuality.status="fully_observed"` is based on network length, not complete upstream signal coverage.

Next step: audit normalization/floors on representative distributions, make adjustments explicit, and separate network presence from source completeness.

## Runtime and cache behavior

[`bootstrap_service.py`](../backend/app/services/bootstrap_service.py), [`graph_service.py`](../backend/app/services/graph_service.py), and route cache release:

- The bootstrap fingerprint does not hash all scoring parameters or source content. Forced derived-cache rebuilding does not force a new graph download.
- Default per-request graph/cache release lowers retained memory but causes reload work on subsequent profile requests. The UI requests alternatives independently.
- Hazard incident loading can still perform network work during routing, even when edge caches are present.
- Synchronous graph/GIS work occurs within route handling. There is no published concurrency/load benchmark.
- Live testing observed intermittent partial comparison failures (including a failed safe profile on a repeated trip and failed fastest/balanced BiciMAD requests). The UI timeout is 180 seconds; request-level backend logs were unavailable, so a specific failure cause was not established.

Next step: reproduce and measure peak memory, latency, and concurrent requests before making optimization claims or broad architectural changes.

## UI and contract coverage

The current `AppLayout` wires the cyclability map, but does not mount the standalone `NeighborhoodCyclabilityPanel` ranking/comparison component. Rankings, detail, and comparison are implemented in services/API and the component exists; they should not all be described as visible panels in the current main screen.

JSON contracts are hand-maintained; some cyclability endpoints return raw dictionaries. The hazard fixture in `test_build_bike_route_uses_bike_leg_hazards` uses an older minimal payload rejected by the current Pydantic response model. No comprehensive provider-backed or browser E2E suite is present.

See [verification](verification.md) for exact test names and observed live behavior. None of these findings demonstrates external safety validation.
