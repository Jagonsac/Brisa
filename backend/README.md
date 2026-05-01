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

- Selección de candidatas por anillos de distancia configurables: `0-400m`, `400-900m`, `900-1500m`, `1500-2200m`.
- Priorización determinista de anillos cercanos y corte temprano cuando ya hay suficientes candidatas prometedoras.
- Evaluación de pares con estrategia `branch-and-bound` usando cotas inferiores admisibles (walking + bike optimistas) para podar combinaciones sin potencial.
- Fallback escalonado en dos etapas (`8x8` y `12x12`) para evitar saltar de forma inmediata a búsqueda exhaustiva.
- Instrumentación interna en metadatos de respuesta: `generatedPairs`, `evaluatedPairs`, `prunedPairs`, `discardedPairs`, y tiempos por fase.

## Testing

```bash
cd backend
pytest
```
