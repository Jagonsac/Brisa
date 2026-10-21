# Routing

Frontend adapters submit one profile per `POST /api/routes` request and display returned GeoJSON, summaries, deterministic explanations, and optional AI insights. The app compares three profiles and optionally night, preserving successful responses after partial failures.

GIS processing and path optimization stay in backend services. See the [routing model](../../../docs/routing-model.md).
