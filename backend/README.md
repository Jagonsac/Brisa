# Brisa Backend

Backend FastAPI para routing ciclista multicriterio de Brisa.

## Endpoints
- `GET /health`
- `GET /api/stations`
- `GET /api/geocoding/suggest`
- `POST /api/routes` (`fastest`, `balanced`, `safe`, `night`)
- `GET /api/cyclability/neighborhoods`
- `GET /api/cyclability/neighborhoods/geojson`
- `GET /api/cyclability/neighborhoods/{id}`
- `GET /api/cyclability/neighborhoods/compare`

## Enfoque de routing (Slice 6.5)
- Unidad de decisión: **edge/tramo**.
- Filtro duro de legalidad ciclista sobre el grafo OSM antes de rutear.
- Métricas de seguridad por edge cacheadas en disco.
- Runtime orientado a lectura de cachés (sin recomputar la red completa en cada request).

## Precompute recomendado
```bash
cd backend
python -m app.pipelines.build_routing_cache
python -m app.pipelines.build_neighborhood_cyclability
```

Esto regenera:
- `backend/data/routing/edge_metrics_<version>.json`
- `backend/data/routing/route_metadata_<version>.json`
- `backend/data/cyclability/neighborhoods_scores.json`
- `backend/data/cyclability/neighborhoods_scores.geojson`

## Arranque local
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
