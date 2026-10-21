# Documentation verification

Audit date: **21 October 2026**. Implementation baseline: [`1523018`](https://github.com/Jagonsac/Brisa/commit/1523018f2500b709cca61cb9dd789d70877a8cc8). No routing or scoring behavior was changed for this documentation work. Basemap fix merge: `7187232d5738c551c2f685674d93f25ab2197238`. The separately requested tile fix is [PR #97](https://github.com/Jagonsac/Brisa/pull/97).

## Hosted application

The live URL, [brisa-madrid.vercel.app](https://brisa-madrid.vercel.app), was discovered in GitHub's repository About metadata, not guessed. Its page returned HTTP 200 and was exercised in a browser.

| Check | Observed result |
| --- | --- |
| Startup and map controls | Application loads; welcome dialog can be dismissed |
| Address suggestions | Entering Matadero Madrid produced a Paseo de la Chopera suggestion that was selected |
| Cycling comparison | The initial run returned all four profiles for Plaza de Castilla → Paseo de la Chopera. A repeat after the tile fix returned fastest, balanced, and night; safe failed in that attempt. Profile reliability is therefore inconsistent. |
| Displayed distances | Fastest 9.15 km; safe 11.66 km; balanced 9.27 km; night 9.27 km |
| Balanced summary | `relativeSafety=high`, `lightingQuality=low`, `nightRisk=medium`; deterministic explanation displayed mean daytime risk 25/100 |
| Night selection | Night route and its explanations rendered; explanation displayed composite night risk 62/100 |
| Cyclability map | Neighborhood polygons and color scale rendered over the routes |
| Safety map | Neighborhood safety layer and hover details rendered before route calculation |
| BiciMAD comparison | Safe (11.89 km, 52 min) and night (9.8 km, 44 min) completed; fastest and balanced failed in this attempt. Station markers rendered. This is partial success, not full multimodal verification. |
| Optional AI | Button present after routes; no paid/provider-backed generation was invoked during the audit |
| Basemap | Initial CARTO tile images displayed `API KEY REQUIRED`; PR #97 was merged and Vercel reported successful production deployment. The production page was reloaded and normal OpenStreetMap tiles were visually verified. |
| Fix validation | Provider selection, key encoding, lint and build passed. After the user resolved the repository review restriction, PR #97 merged and the production map was verified. The authenticated CARTO-key path remains unverified without a real key. |

The publicly accessible [Loom walkthrough](https://www.loom.com/share/394337e4a7da452c9a4c78ba2a633dac) has a Spanish summary and chapters at 0:00, 0:48, and 1:38. Its player reports approximately 2:54 at normal speed. It is linked as a Spanish-language recording, not an English demo.

## Screenshot provenance

All final assets come from the live production application after basemap fix `7187232`. The initial audit's longer-trip results are retained as textual observations; screenshots show a later shorter trip.

| Asset | Source / state |
| --- | --- |
| [overview.jpg](assets/overview.jpg) | Live planning interface with the repaired OpenStreetMap background, before a route is requested |
| [route-comparison.jpg](assets/route-comparison.jpg) | Completed Puerta del Sol → Intercambiador de Atocha comparison; four profiles returned 2.05 km, balanced selected |
| [night-routing.jpg](assets/night-routing.jpg) | Same completed short trip, night profile selected |
| [night-routing-detail.jpg](assets/night-routing-detail.jpg) | Crop of the actual night summary: medium relative safety, low lighting quality, high night risk; explanation reports 70/100 |
| [cyclability-map.jpg](assets/cyclability-map.jpg) | Live neighborhood cyclability choropleth after layers finished loading; no route requested in this capture |

Captures are optimized progressive JPEGs under `docs/assets/`. No generated imagery, mock routes, fabricated results, or replacement map background was substituted. A fresh production page was opened after deployment; the clean map comes from the deployed tile fix. A normal map zoom adjustment was used to show route context.

The final short trip completed all four profiles, displaying 7/9/8/9 minutes for fastest/safe/balanced/night respectively. Those estimates use different fixed speeds, not measured journey times. The longer-trip repeat and BiciMAD partial failures remain recorded above; selecting a successful screenshot does not establish general reliability.

## Local checks

Environment: Python 3.12; Node 24.19.0; npm 11.9.0. Dependencies installed from the existing package manifests without a committed lockfile or dependency upgrades.

| Command | Result |
| --- | --- |
| `npm install --package-lock=false --ignore-scripts` | Completed |
| `npm run lint` | Passed on the baseline and basemap-fix code |
| `npm run build` | Passed on the baseline and basemap-fix code |
| `python -m pip install -r requirements.txt pytest pytest-asyncio` | Completed in an isolated environment |
| `PRECOMPUTE_CACHE_ON_STARTUP=false python -m pytest -q` from `backend/` | **20 passed, 4 failed**, one dependency deprecation warning |

The four failures were present before documentation changes:

| Test | Observed cause |
| --- | --- |
| `test_green_cyclable_score_rewards_legal_green_network` | Two-row floor-index percentile bounds collapse; both green components become 50 |
| `test_served_area_ratio_reduces_large_area_penalty` | Both fixture examples reach the 0.15 floor |
| `test_branch_and_bound_prunes_pairs` | Current one-pair search evaluates one pair with and without bounding |
| `test_build_bike_route_uses_bike_leg_hazards` | Fixture uses an older minimal hazard payload; current response validation requires additional fields |

Tests ran against the unchanged implementation. Tests primarily use stubs/fixtures. No independent safety calibration, full GIS preprocessing run, load benchmark, or broad browser E2E suite was performed or claimed. A full local city-data rebuild was not required because the hosted app returned real routes.

## Formula checks

Every displayed profile coefficient was checked against `routing_profiles.py` and `_decorate_graph_weights`. Day/night weights, clipping, smoothing priors, radii, signal divisor, road hostility and infrastructure treatment were checked against `safety_config.py`, `edge_safety_service.py`, and `bike_legality_service.py`. The [model guide](routing-model.md) distinguishes raw signals, stored metrics, path objectives, and summary aggregation.

## Links and rendering

Local Markdown/image paths and fragment targets are checked as part of the documentation review. JSON contracts are parsed for syntax; they have not all been automatically validated against live payloads. The main README is reviewed on its GitHub branch for actual math, image, and Mermaid rendering before delivery.

External URLs depend on provider availability. The live app and Loom returned HTTP 200. The three problematic municipal catalog defaults (`IMD_CSV_URL`, `CROSSINGS_CSV_URL`, `BIKE_CROSSINGS_CSV_URL`) returned HTTP 200 with **text/html**, confirming that a successful HTTP request alone does not make them valid CSV inputs. Other upstream access failures are reported separately from local broken links.

The broader external-link check found the configured monthly traffic API returning HTTP 404 and the EMT portal homepage returning HTTP 500. The documentation uses the working EMT dataset link instead of its failing homepage, and retains the configured traffic API URL as an explicitly reported implementation issue. All other checked municipal CSV resources, GBFS/EMT location resources, and the primary boundary GeoJSON returned HTTP 200. Nominatim and the OSMF policy page timed out from the local checker; OSMF policy content was independently retrieved from the official site, and Nominatim-backed suggestions worked in the hosted app. Loom was accessible in the browser and an earlier HTTP check, despite a later timeout. These checks establish access at audit time, not future provider availability.

Local validation: **115 relative links/fragments resolved**, **11 JSON contracts parsed**, math/code fences balanced, and `git diff --check` passed.
