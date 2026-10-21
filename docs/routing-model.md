# Routing model

This document describes the implementation in [RouteService](../backend/app/services/route_service.py), [EdgeSafetyService](../backend/app/services/edge_safety_service.py), [GraphService](../backend/app/services/graph_service.py), and [bike_legality_service.py](../backend/app/services/bike_legality_service.py). Values below are defaults, not empirically fitted parameters.

## 1. Network and path search

OSMnx builds a simplified directed multigraph from `OSMNX_PLACE_QUERY` (default `Madrid, Spain`). `OSMNX_NETWORK_TYPE` defaults to `all` in code; the older backend example environment suggests `bike`, which yields a different base graph. A derived graph filters motorways, `motorroad=yes`, `bicycle=no`, certain `access=no` edges, and trunk roads without explicit cycling infrastructure. These are implemented tag rules, not a complete legal-access validator: private access, conditional restrictions, missing tags, turn restrictions, and directional cycling exceptions need further work.

The pinned OSMnx defaults do not retain several bicycle-specific tags, and `GraphService` does not extend `useful_tags_way`. The scorer/filter can use those tags when present in a supplied cache, but fresh default builds may lack them. See the [tag-retention issue](known-issues.md#osm-bicycle-tags-need-explicit-retention).

Edges are keyed by `u:v:key`, preserving parallel directed segments. Length is the OSMnx `length` attribute. Endpoints snap with `ox.distance.nearest_nodes`; if optional spatial dependencies are missing, a NumPy fallback minimizes squared latitude/longitude differences. That fallback is an approximation in angular coordinates.

`nx.shortest_path` with an edge-weight attribute uses NetworkX's weighted Dijkstra path machinery (the single-source/target case uses bidirectional Dijkstra in NetworkX 3.5). Brisa does not implement a custom search algorithm. For each node pair on the path, it selects the parallel edge with minimum profile cost and assembles its geometry.

```math
P_m^*=\arg\min_{P:s\leadsto t}\sum_{e\in P}w_m(e)
```

Costs are nonnegative with the supplied defaults. Environment overrides are parsed as numbers but not validated to preserve that property. There is no hard bound on detour length, slope model, signal-delay model, live congestion model, or Pareto-frontier search.

## 2. Municipal signals at a road segment

Let $c(x)=\min(1,\max(0,x))$. Geometry samples are transformed from WGS84 (`EPSG:4326`) to ETRS89 / UTM zone 30N (`EPSG:25830`) so distances are in meters.

For a geometry with at most three vertices, every vertex is sampled. With more vertices, only the first, middle-index, and last are used. Without a geometry, the endpoints and their coordinate midpoint are sampled. These are not samples uniformly spaced by length.

A 120 m bucket index limits point searches. For source $k$, sample $q$, record $p_i$ with value $v_i$, and radius $r_k$, define:

```math
S_k(q)=\sum_{i: d(q,p_i)\leq r_k}\frac{v_i}{1+\max(1,d(q,p_i))/20}
```

```math
s_k(e)=c\left(\frac{1}{12\lvert Q_e\rvert}\sum_{q\in Q_e}S_k(q)\right)
```

The divisor 12 is `SAFETY_SIGNAL_SCALE_DIVISOR`. It is a fixed scale followed by saturation, **not** dataset-wide min-max scaling or probability calibration. Different source units pass through the same scale.

| Signal | Symbol | Default radius | Loader behavior |
| --- | --- | ---: | --- |
| General incidents | $g$ | 30 m | UTM records weighted by injury severity |
| Cycling incidents | $b$ | 30 m | Same treatment, retaining vehicle descriptions containing `bicic` |
| Nighttime incidents | $a$ | 30 m | General incident source, hours 22:00–05:59 |
| Non-permanent motor counts | $T$ | 50 m | First available total/light-vehicle/intensity/IMD value |
| Mean daily motor traffic | $I$ | 65 m | First available intensity/IMD/value/total field |
| Streetlights | $\ell$ | 35 m | Each accepted UTM point contributes 1 |
| Cycling counts | $P$ | 45 m | `bicicletas` field, with configured loader fallback |
| Crossings | $X$ | 40 m | Current loader uses numeric `id`/`codigo` as value, not a unit count |
| Bicycle crossings | $X_b$ | 40 m | Same identifier-weighting caveat |

Incident values are 1.0 for numeric injury codes ≤3, 0.7 for codes ≤7, and 0.45 otherwise. Without a numeric code, labels containing `grave`/`falle` give 1.0, `leve` gives 0.55, and other labels give 0.6. These are the parser's rules, not a validated interpretation of every source codebook. Unlike the separate map incident loader, this edge loader does not deduplicate rows by incident ID; multiple records can influence a location.

Downloads write raw CSV files and reuse them after download failures. Without a cached file, a failed source produces no points. Missing or unrecognized coordinate columns also produce no points. Inspect the per-source `records` metadata rather than assuming all configured sources were observed. The night hour window is configurable through `NIGHT_START_HOUR` and `NIGHT_END_HOUR`; it does not use sunset or the requested departure time.

## 3. Infrastructure, hostility, and junctions

The OSM infrastructure score $O$ is:

- 1.0 for `highway=cycleway` (returned immediately).
- Otherwise, 0.9 for `track`, `separate`, or `opposite_track`; 0.55 for `lane`, `opposite_lane`, or `shared_lane`; 0.35 for other nonempty cycleway tokens.
- `bicycle=designated` raises that score to at least 0.45; `segregated=yes` adds 0.15, capped at 1.

The code checks `cycleway`, `cycleway:left`, `cycleway:right`, and `cycleway:both`. It does not measure width, surface quality, physical separation quality, or infrastructure continuity.

For parsed lane count $n$, speed limit $v$ in km/h, and road-class base $h$:

```math
H=c\left(h+0.45\min(1,n/4)+0.40\min(1,v/50)-0.55O\right)
```

| OSM highway class | Base $h$ |
| --- | ---: |
| cycleway / living_street | 0.08 / 0.12 |
| residential / service / unclassified | 0.25 / 0.25 / 0.30 |
| tertiary / tertiary_link | 0.52 / 0.58 |
| secondary / secondary_link | 0.72 / 0.78 |
| primary / primary_link | 0.88 / 0.90 |
| trunk / trunk_link | 0.98 / 0.99 |
| Unlisted | 0.45 |

Absent lane/speed tags default to 1 lane and 30 km/h. Parsed values are bounded to 1–8 lanes and 10–120 km/h. Lists are averaged; tag parsing is heuristic and can mishandle compound speed strings. Highway lists use the first entry.

For endpoint degrees in the directed multigraph:

```math
J=c\left(0.65\frac{\min(8,\deg u)+\min(8,\deg v)}{16}+0.35X\right)
```

Graph degree counts incoming/outgoing and parallel edges; it is a proxy for complexity, not the number of physical junction approaches.

Cycling relief and lighting deficit are:

```math
B=c(0.25P+0.65O+0.20X_b),\qquad D=1-c(\ell)
```

Thus OSM infrastructure acts twice: directly on hostility and through the cycling bonus. Cycling counts are also a bonus, not a measured denominator of cyclist exposure.

## 4. Smoothed incident signals

With prior mean $\mu=0.18$ and strength $\alpha=3.5$:

```math
f(o,x)=\frac{o+\alpha\mu}{\max(x,0.1)+\alpha}
```

```math
\begin{aligned}
A_g&=c(f(g,L/100+T+J))\\
A_b&=c(f(b,L/120+0.6T))\\
A_n&=c(f(a,L/140+T))
\end{aligned}
```

Here $g,b,a$ are already normalized local signals. Length and traffic form a heuristic exposure proxy with mixed units; these are not accident counts divided by observed journeys. Smoothing avoids interpreting zero nearby observations as definitive zero risk. It also means a missing incident source need not produce a zero smoothed score.

## 5. Day and night risk

```math
R=c(0.30H+0.25c(0.6T+0.4I)+0.12J+0.20A_g+0.08A_b-0.16B)
```

```math
N=c(R+0.28D+0.22A_n+0.20c(0.7I+0.3T)+0.10J)
```

These weights live in [safety_config.py](../backend/app/core/safety_config.py) under `day_weights` and `night_weights`, with `SAFETY_DAY_W_*` and `SAFETY_NIGHT_W_*` environment overrides. The sums are not normalized by the total weight; the resulting value is clipped. The stored `motorTrafficExposureScore` uses $c(0.5T+0.5I)$, which differs from both blends inside the risk equations.

## 6. Profile costs and configuration

```math
\begin{aligned}
w_{\mathrm{fastest}}&=L[1+0.5\max(0,H-0.85)]\\
w_{\mathrm{safe}}&=L[1+4.2R]\\
w_{\mathrm{balanced}}&=L[1+2.1R]\\
w_{\mathrm{night}}&=L[1+4.5R+2.4D+1.6N]
\end{aligned}
```

| Environment variable | Default |
| --- | ---: |
| `FASTEST_EXTREME_HOSTILITY_MULTIPLIER` | 0.5 |
| `SAFE_RISK_MULTIPLIER` | 4.2 |
| `BALANCED_RISK_MULTIPLIER` | 2.1 |
| `NIGHT_BASE_RISK_MULTIPLIER` | 4.5 |
| `NIGHT_LIGHTING_MULTIPLIER` | 2.4 |
| `NIGHT_ACCIDENT_MULTIPLIER` | 1.6 |

The final variable's name is historical: it multiplies $N$, the entire night score. Since $N$ contains $R$, $D$, and $J$, the final night objective repeats these influences; it is not a set of independent factors. Clipping makes the effective influence nonlinear.

Missing edge metrics default to $R=0.45,D=0.5,N=0.35,H=0.5$ when graph weights are attached. Cached metrics are rounded to six decimals. Changing routing multipliers changes attached costs at process startup; changing signal weights requires rebuilding edge metrics and downstream cyclability caches.

## 7. Summaries, hazards, and alternatives

For a route with $k$ selected edges, summary risk is $\bar R=k^{-1}\sum_e R(e)$, **not** $\sum_e L(e)R(e)/\sum_e L(e)$. Lighting and night summaries use the same unweighted averaging. Day safety and lighting quality are `high` at ≤0.33, `medium` at ≤0.66, otherwise `low`; night risk reverses the favorable direction.

Detour explanations compare distance against a separate pure-`length` shortest path, which can differ from `fastest`. The frontend derives ordinary cycling durations from mode-specific assumed speeds; multimodal durations use 1.32 m/s walking and 4.2 m/s cycling. Neither is a predictive travel-time model.

Hazards are computed deterministically using thresholds and supporting source fields. Matching currently measures distance to route vertices, not a perpendicular distance to every line segment, so events beside sparsely sampled geometry can be missed. The optional AI service receives summaries and up to 20 hazards per route, and produces text; it cannot modify path geometry or scores.

The frontend requests three or four profiles with `Promise.allSettled`. This supports partial success, not a single shared server-side multi-profile computation. Identical paths and a safe path with the same coarse label as a faster path are valid outcomes.

## 8. Separate map and neighborhood models

The safety map uses a 250 m grid, independently normalized incident/traffic/road/infrastructure signals, and a neighborhood aggregation. Routing responses explicitly set `usedSafetyGrid`, `usedLightingGrid`, and `usedNightRiskGrid` to false.

Cyclability aggregates directed edge lengths into neighborhoods, normalizes seven components with clipped 5th/95th percentile bounds, applies technical floors, and takes a weighted mean. Green-area rebalancing can then raise the score. Casa de Campo and Los Jerónimos have a named minimum of `max(current, CYCLABILITY_PARK_FLOOR_HIGH, 72)`; that override runs before the general rebalancing-enabled check. A debug breakdown exposes `rebalancing`, so the standard component contributions alone may not sum to the final adjusted score.

These outputs answer different questions. None should be read as an externally validated safety rating. See [data sources](data-sources.md) and [known issues](known-issues.md).
