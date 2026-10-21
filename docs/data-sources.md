# Data sources and provenance

Brisa uses a street graph, point-based municipal signals, administrative boundaries, and station locations. A URL in configuration identifies an intended source; it does **not** prove that a preprocessing run loaded usable records. Check metadata, coordinate columns, and source dates.

## Input map

| Input | Consumer | Role / caveat |
| --- | --- | --- |
| OpenStreetMap via OSMnx / Overpass | `GraphService` | Directed base network, road lengths and tags; cycling-access filtering; separate walking graph |
| General traffic incidents | `EdgeSafetyService` | Severity-weighted daytime and nighttime point signals; edge loader does not deduplicate incident rows |
| Bicycle traffic incidents | Edge safety; `AccidentDataService` for map/hazards | Edge proximity signal; separate map loader groups records by incident ID and uses its own severity rules |
| Non-permanent motor counts | Edge safety | Local traffic signal; source values and coordinate-column coverage affect scale |
| Mean daily traffic (IMD) | Edge safety | Supplemental motor exposure; default is a catalog page rather than CSV |
| General / bicycle signalized crossings | Edge safety | Junction and cycling signals; defaults are catalog pages, and numeric IDs currently act as weights |
| Streetlight inventory | Edge safety | Nearby point density as lighting proxy; does not measure illumination or lamp operating state |
| Pedestrian/bicycle counts | Edge safety | Cycling presence; only records with recognized coordinates/fields contribute |
| Permanent traffic stations + monthly API | `TrafficDataService`, safety grid | Separate grid traffic model with fallback behavior; not the active edge traffic pipeline |
| Neighborhood boundaries | `NeighborhoodService` | Grid aggregation and edge-to-neighborhood assignment |
| GBFS station information / EMT GeoJSON | `BicimadService` | Station locations with provider and snapshot fallbacks |
| Local BiciMAD location snapshot | `CyclabilityService` | Station density and geometric 400 m buffer coverage; not live availability |
| CARTO / OpenStreetMap raster tiles | React Leaflet | Visual background only; not an input to route scoring. See [tile configuration](map-tiles.md). |

Source ownership and attribution: [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), [Madrid Open Data](https://datos.madrid.es/), and [EMT station data](https://datos.emtmadrid.es/dataset/5fcc0945-2cbd-46c3-801a-6a83f4167c11/resource/105ce5df-793f-4e0a-a88e-5d3b3f024a5d/download/bikestationbicimad_geojson.geojson). The repository's MIT license applies to code, not automatically to downloaded datasets or third-party map tiles. Check each publisher's current reuse terms and keep source attribution.

## Configured municipal URLs

The following table reflects `SafetyConfig`. URLs may redirect or change upstream; use direct CSV/GeoJSON/API resources with the fields the corresponding loader expects. Overriding a URL without validating its schema is insufficient.

| Environment override | Default link | Expected input / note |
| --- | --- | --- |
| `GENERAL_ACCIDENTS_CSV_URL` | [Configured source](https://datos.madrid.es/dataset/300228-0-accidentes-trafico-detalle/resource/300228-34-accidentes-trafico-detalle/download/300228-34-accidentes-trafico-detalle.csv) | API / CSV resource |
| `BIKE_ACCIDENTS_CSV_URL` | [Configured source](https://datos.madrid.es/dataset/300110-0-accidentes-bicicleta/resource/300110-0-accidentes-bicicleta-csv/download/300110-0-accidentes-bicicleta-csv.csv) | API / CSV resource |
| `TRAFFIC_NON_PERMANENT_CSV_URL` | [Configured source](https://datos.madrid.es/dataset/300209-0-aforos-no-permanentes/resource/300209-1-aforos-no-permanentes-csv/download/300209-1-aforos-no-permanentes-csv.csv) | API / CSV resource |
| `IMD_CSV_URL` | [Configured source](https://datos.madrid.es/dataset/203962-0-trafico-imd) | Catalog HTML; CSV override needed |
| `CROSSINGS_CSV_URL` | [Configured source](https://datos.madrid.es/dataset/300275-0-cruces-semaforizados) | Catalog HTML; CSV override needed |
| `BIKE_CROSSINGS_CSV_URL` | [Configured source](https://datos.madrid.es/dataset/205159-0-bici-cruces-semaforizados) | Catalog HTML; CSV override needed |
| `LIGHTING_CSV_URL` | [Configured source](https://datos.madrid.es/dataset/300573-0-unidades-luminosas-farolas/resource/300573-0-unidades-luminosas-farolas-csv/download/300573-0-unidades-luminosas-farolas-csv.csv) | API / CSV resource |
| `BIKE_COUNTS_CSV_URL` | [Configured source](https://datos.madrid.es/dataset/300321-0-aforos-peatones-bicicletas/resource/300321-10-aforos-peatones-bicicletas-csv/download/300321-10-aforos-peatones-bicicletas-csv.csv) | API / CSV resource |
| `SAFETY_TRAFFIC_STATIONS_CSV_URL` | [Configured source](https://datos.madrid.es/dataset/300233-0-aforo-trafico-permanentes/resource/300233-112-aforo-trafico-permanentes-csv/download/300233-112-aforo-trafico-permanentes-csv.csv) | API / CSV resource |
| `SAFETY_TRAFFIC_MONTHLY_API_URL` | [Configured source](https://datos.madrid.es/api/3/action/datastore_search?resource_id=300233-6-aforo-trafico-permanentes-xlsx&limit=50000) | API / CSV resource |
| `SAFETY_NEIGHBORHOODS_GEOJSON_URL` | [Configured source](https://sigma.madrid.es/hosted/rest/services/CARTOGRAFIA/LIMITES_ADMINISTRATIVOS/MapServer/25/query?where=1%3D1&outFields=COD_BAR%2CNOMBRE%2CNOMDIS&outSR=4326&f=geojson) | GeoJSON API |

The monthly traffic API default returned **HTTP 404** during the audit; the grid traffic service has fallback logic, and metadata should be checked for its use. The three catalog defaults returned HTML as noted above. The remaining CSV defaults, station feeds, and primary boundary GeoJSON returned HTTP 200 at check time.

Neighborhood boundaries also try the two fallback URLs in `safety_config.py` and the local raw cache. A bundled `madrid_barrios_131.geojson` file is present, but the loader's configured filename defaults to `madrid_barrios.geojson`; do not assume the bundled filename is automatically selected.

BiciMAD defaults in [config.py](../backend/app/core/config.py):

- `BICIMAD_STATIONS_URL`: [GBFS station information](https://madrid.publicbikesystem.net/customer/gbfs/v2/es/station_information).
- `BICIMAD_FALLBACK_URL`: [EMT station GeoJSON](https://datos.emtmadrid.es/dataset/5fcc0945-2cbd-46c3-801a-6a83f4167c11/resource/105ce5df-793f-4e0a-a88e-5d3b3f024a5d/download/bikestationbicimad_geojson.geojson).
- `BICIMAD_STATUS_URL` and its service exist, but active route station selection does not use them.

Geocoding defaults to [Nominatim](https://nominatim.openstreetmap.org/). Supply an application/contact user agent for hosted use and respect the provider's access policy. Optional AI insight requests go to [OpenAI's Responses API](https://platform.openai.com/docs/api-reference/responses); no AI response is a source of graph or score data.

## Coordinates and sampling

Map and route output use WGS84 longitude/latitude (`EPSG:4326`). Metric proximity/area operations use ETRS89 / UTM zone 30N (`EPSG:25830`). Accident and lamp loaders expect specific UTM fields; traffic/count sources need recognized latitude/longitude fields. Invalid/missing coordinates are skipped rather than geocoded from address text. The graph builder does not explicitly extend OSMnx's retained way tags, so bicycle-specific attributes can be absent on fresh default downloads; see the [tag-retention finding](known-issues.md#osm-bicycle-tags-need-explicit-retention).

The edge pipeline samples at most three geometry vertices, uses a distance-decayed local sum, and clips after a fixed scale divisor. Its radii and smoothing equations are in the [routing model](routing-model.md). Grid safety normalizes across cells independently. The neighborhood index aggregates mostly by edge length; directed/parallel edges are counted as graph edges, not deduplicated physical street centerlines.

## Freshness, missingness, and reproducibility

- GraphML and processed JSON/GeoJSON are reused from disk. Freshness is not guaranteed merely by restarting the API.
- The edge CSV loader tries a fresh download and falls back to its raw cache on request failure; without a raw cache it returns an empty source. HTML or unmatched columns can also yield zero usable points.
- `edge_metrics_<version>.json` and routing metadata include source record counts and generation time. Counts alone do not establish temporal coverage, completeness, or source validity.
- `route_metadata_<version>.json` records profile multipliers and the configured night window. Cyclability metadata records its normalization settings and station count.
- Not every dependent service follows the same cache/fallback policy; for example, hazard incident loading can still depend on a fresh request. A previously successful edge build does not make the entire application offline-capable.
- A small station snapshot is bundled for fallback; successful remote station loads overwrite it when writable. Neighborhood scores can change depending on the snapshot available during preprocessing.
- There is no immutable data release, global source checksum manifest, or comprehensive automatic freshness/confidence policy. Rebuild commands and current defaults aid reproduction but do not guarantee bit-identical scores months later.

For troubleshooting zero records and refresh order, see [backend operations](../backend/README.md#preprocessing-and-cache-refresh). For recorded link checks and runtime observations, see [verification](verification.md).
