# Roadmap

The codebase implements a cycling planner, edge-based profile costs, map safety, neighborhood cyclability, station-location integration, BiciMAD legs, and optional AI interpretation. This describes implemented scope, not a claim of production reliability or validated safety. See [verification](verification.md) for observed runtime behavior and test results.

## Near-term priorities

| Priority | Work | Evidence of completion |
| --- | --- | --- |
| Delivered | Restore basemap access | PR #97 merged: key-free OSM default, optional CARTO key; production verification recorded separately |
| High | Resolve the four existing test failures | Reconcile percentile/floor expectations, station-search assumptions, and hazard fixtures; retain meaningful assertions |
| High | Validate municipal source ingestion | Direct resource URLs, schema checks, nonzero record diagnostics, and explicit missing-data warnings |
| High | Correct misleading explanation text | Align BiciMAD availability and time-optimization wording with actual behavior |
| High | Add integration and browser coverage | Exercise a representative trip across all profiles, map layers, partial failure, and BiciMAD legs |
| Medium | Restore availability-aware BiciMAD ranking | Use fresh station status with deterministic proximity fallback and more than one feasible pair |
| Medium | Improve scoring transparency | Audit identifier-weighted crossings, named park overrides, directed-edge aggregation, and exposure proxies |
| Medium | Version inputs and caches comprehensively | Hash/fingerprint relevant configuration and source snapshots; document controlled rebuilds |
| Medium | Measure and improve GIS runtime/memory | Publish reproducible measurements before claiming improvements |
| Medium | Add public CI and release policy | Lint/build/backend checks, documented baseline, semantic versioning |
| Later | External model calibration | Compare against independent observations; test sensitivity and uncertainty |
| Later | Internationalization and accessibility | English/Spanish UI, keyboard workflows, and audited contrast/labels |

The optional AI layer remains an explanation feature; it is not a replacement for deterministic routing or model validation. Proposed items above are not delivered features.

Detailed historical development notes remain in [slices/](slices/README.md). They describe earlier stages and can differ from current behavior; code and the current technical guides take precedence.
