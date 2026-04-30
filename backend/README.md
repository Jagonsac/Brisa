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
python -m app.pipelines.build_neighborhood_cyclability
```

Esto genera/actualiza artefactos en `backend/data/` para acelerar peticiones y evitar recomputación pesada.

## Principios de implementación

- Routers finos + servicios de dominio dedicados.
- Contratos estables en `backend/app/schemas` y `docs/contracts`.
- Normalización de proveedores externos aislada en `clients`/`utils`.
- Lógica GIS y de scoring mantenida exclusivamente en backend.

## Testing

```bash
cd backend
pytest
```

