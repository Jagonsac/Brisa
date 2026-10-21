# UI state notes

These notes describe the current [`AppLayout`](../../src/app/layout/AppLayout.jsx) state, not a serialized API response or an enforced runtime schema.

| State | Meaning |
| --- | --- |
| `inputValues.origin`, `inputValues.destination` | Search-field strings |
| `selectedPlaces.origin`, `selectedPlaces.destination` | Optional selected/geolocated coordinates used in route requests |
| `selectedRouteMode` | `fastest`, `safe`, `balanced`, or `night`; initially `balanced` |
| `routesByMode` | Successfully returned routes keyed by requested profile |
| `includeNightRoute` | Add night profile to the three default comparisons |
| `useBicimadRouting` | Request walking/cycling/walking station-based legs |
| `routeLoading`, `routeError`, `infoMessage` | Progress, error, and user-facing status |
| `activeInsightLayer` | `safety`, `cyclability`, or `none`, subject to layer availability |
| `aiInsights`, `aiInsightsLoading`, `aiInsightsError` | Optional analysis state, independent of path computation |

The UI gathers profile requests with `Promise.allSettled`. Partial success is retained and failed profile names are displayed. Existing routes can remain visible while a new comparison is loading; screenshots used as results must be captured after completion and checked for partial errors.

API mode names use `fastest`, not the earlier `fast` placeholder. The request/response boundary is specified in [route-request](route-request.contract.json) and [route-response](route-response.contract.json).
