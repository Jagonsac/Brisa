# Brisa Backend

API FastAPI para geocoding, routing ciclista multicriterio, multimodal Bicimad, safety y ciclabilidad por barrios.

## Requisitos

- Python 3.10+
- Dependencias en `requirements.txt`

## Arranque local

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Endpoints

- `GET /health`
- `GET /api/stations`
- `GET /api/geocoding/suggest`
- `GET /api/safety/grid`
- `GET /api/safety/summary`
- `GET /api/cyclability/neighborhoods`
- `GET /api/cyclability/neighborhoods/geojson`
- `GET /api/cyclability/neighborhoods/{id}`
- `GET /api/cyclability/neighborhoods/compare`
- `POST /api/routes`

## Precompute recomendado

```bash
cd backend
python -m app.pipelines.build_routing_cache
python -m app.pipelines.build_safety_cache
python -m app.pipelines.build_neighborhood_cyclability
```

Esto genera/actualiza artefactos en `backend/data/` para acelerar peticiones y evitar recomputación pesada.

En particular, `python -m app.pipelines.build_routing_cache` genera `backend/data/routing/edge_metrics_<version>.json` (con métricas por arista, incluido riesgo nocturno) y `route_metadata_<version>.json`, que se cargan en runtime para evitar reconstrucción completa en cada petición de rutas.

### Artefactos esperados de safety

Tras ejecutar el precompute de safety (o al arrancar la API con `PRECOMPUTE_CACHE_ON_STARTUP=true`), deben existir:

- `backend/data/safety/processed/madrid_safety_grid_v1.geojson`
- `backend/data/safety/processed/safety_metadata_v1.json`
- `backend/data/safety/processed/madrid_safety_neighborhood_grid_v2.geojson`
- `backend/data/safety/processed/safety_neighborhood_metadata_v2.json`

Si faltan, el backend intentará reconstruirlos en la primera petición a `/api/safety/*`.

## Principios de implementación

- Routers finos + servicios de dominio dedicados.
- Contratos estables en `backend/app/schemas` y `docs/contracts`.
- Normalización de proveedores externos aislada en `clients`/`utils`.
- Lógica GIS y de scoring mantenida exclusivamente en backend.

## Optimización multimodal Bicimad (selección de estaciones)

- Estrategia deliberadamente simple para priorizar latencia: estación de salida más cercana al origen y estación de llegada más cercana al destino (distinta de la de salida).
- Se evalúa una sola combinación de estaciones (best-effort) para minimizar tiempos de respuesta.
- Instrumentación interna en metadatos de respuesta: `generatedPairs`, `evaluatedPairs`, `discardedPairs`, y tiempos por fase.

## Testing

```bash
cd backend
pytest
```
