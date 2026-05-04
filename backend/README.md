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

## Precompute automático en startup (producción)

Al arrancar la API, `BootstrapService` prepara todo lo pesado para que no lo pague el primer usuario:

- carga/descarga grafos OSM (`data/graphs`)
- genera cache de routing (`data/routing`)
- genera safety grid + safety por barrio (`data/safety/processed`)
- genera ciclabilidad por barrio (`data/cyclability`)
- guarda estado de bootstrap en `data/cache/bootstrap_state_v1.json`

Variables de entorno:

- `PRECOMPUTE_CACHE_ON_STARTUP=true` (recomendado en Railway)
- `FORCE_REBUILD_CACHE_ON_STARTUP=false` (poner `true` solo cuando quieras recalcular todo)
- `RISK_MATCH_RADIUS_M=45` radio (metros) para considerar que la ruta pasa por un evento puntual real.
- `JUNCTION_RISK_MIN=0.7` umbral mínimo del `junctionComplexityScore` para reportar `dangerous_junction`.
- `ACCIDENT_HOTSPOT_MIN=0.75` umbral mínimo de severidad agregada para reportar `bike_accident_hotspot`.
- `LOW_CYCLABILITY_PERCENTILE_MAX=10` percentil máximo para reportar `low_cyclability_neighborhood`.

## Guía de deploy backend en Railway (paso a paso)

1. Crea un servicio en Railway apuntando a este repo y selecciona el directorio `backend` como root del servicio.
2. Añade un **Volume** al servicio y móntalo en `/app/data`.
3. Configura variables de entorno:
   - `PRECOMPUTE_CACHE_ON_STARTUP=true`
   - `FORCE_REBUILD_CACHE_ON_STARTUP=false`
   - `BRISA_ENV=production`
   - `FRONTEND_ORIGINS=https://<tu-frontend-vercel>.vercel.app`
   - `NOMINATIM_USER_AGENT=Brisa/1.0 (production contacto@tu-dominio)`
4. En Settings del servicio, define Start Command:
   - `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Lanza el primer deploy.
6. Revisa logs del deploy hasta ver que termina el bootstrap y que arranca Uvicorn.
7. Verifica salud:
   - `GET /health`
   - `GET /api/safety/summary`
   - `GET /api/cyclability/neighborhoods`
8. Haz un segundo deploy (sin tocar datos). Debe arrancar rápido y reutilizar `data/*` del volumen sin recomputar.
9. Si alguna vez quieres regenerar todo por cambios de modelo/datos, cambia temporalmente:
   - `FORCE_REBUILD_CACHE_ON_STARTUP=true`
   - redeploy
   - vuelve a `false` al terminar.

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
