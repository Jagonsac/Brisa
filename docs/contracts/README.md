# Frontend/backend contracts

This directory documents Brisa's internal public payloads, insulating the UI from raw provider schemas. Python models live in [`backend/app/schemas`](../../backend/app/schemas); frontend HTTP/normalization adapters live under `src/features/*/services` and `utils`.

These are hand-maintained JSON Schema documents and mapping notes, not a generated typed frontend client. Some API endpoints return dictionaries without a declared Pydantic response model, and comprehensive automatic schema-conformance tests are still needed. Consult the routers and the running API's `/docs` for implemented parameters.

| Boundary | Contract |
| --- | --- |
| Health | [health-response](health-response.contract.json) |
| BiciMAD locations | [stations](stations.contract.json), [provider mapping](stations.mapping.md) |
| Geocoding suggestions | [geocoding-suggest-response](geocoding-suggest-response.contract.json) |
| Routing | [route-request](route-request.contract.json), [route-response](route-response.contract.json) |
| Optional AI interpretation | [ai-route-insights](ai-route-insights.contract.json) |
| Safety map | [safety-grid-response](safety-grid-response.contract.json), [safety-summary-response](safety-summary-response.contract.json) |
| Neighborhood cyclability | [cyclability-neighborhoods](cyclability-neighborhoods.contract.json), [neighborhood-score](neighborhood-score.contract.json) |
| Score debug endpoint | [cyclability-score-breakdown](cyclability-score-breakdown.contract.json) |
| UI state notes | [ui-state](ui-state.contract.md) |

## Important semantics

- `mode` selects `fastest`, `safe`, `balanced`, or `night`. Each route request calculates one profile.
- `useBicimad=true` adds walking/cycling/walking legs. The returned summary mode can be `bicimad`; `bikeProfile` retains the cycling preference.
- `relativeSafety`, `lightingQuality`, and `nightRisk` are qualitative heuristic labels, not calibrated probabilities.
- `liveStatusUsed=false` in current multimodal responses; bike/dock counts are null. Do not interpret `isOperational=true` in the station payload as a verified live status.
- `usedSafetyGrid`, `usedLightingGrid`, and `usedNightRiskGrid` are false on the active edge-based routing path.
- Hazard evidence is generated deterministically; AI interpretation is optional and separate.
- Neighborhood comparison query parameters are `left` and `right`, not `a` and `b`.
- Scores can include `rebalancing`; standard component contributions alone may differ from the final neighborhood total.

When changing a payload, update its contract, relevant models/adapters, documentation, and meaningful tests in the same pull request. Preserve required/optional field semantics and document breaking changes explicitly. Historical Spanish descriptions and implementation notes remain in individual schemas and archived slice documents.
