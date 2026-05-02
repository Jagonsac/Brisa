# Brisa 🚲

Brisa es una plataforma open source para planificar rutas ciclistas en Madrid combinando **rapidez, seguridad y contexto urbano**. Incluye frontend React (mapa interactivo) y backend FastAPI (geocoding, routing multicriterio, seguridad, ciclabilidad por barrios y soporte multimodal con Bicimad).

## Estado del proyecto

**Versión funcional actual:** cierre de desarrollo interno tras completar las fases 1–9.

Capacidades principales disponibles:
- Routing real sobre red OSM para modos `fastest`, `safe`, `balanced` y `night`.
- Comparativa de rutas y resumen explicable por métricas.
- Soporte multimodal opcional con Bicimad (`walk + bike + walk`).
- Capa de seguridad ciclista y resumen agregado de riesgo.
- Índice de ciclabilidad por barrio (listado, detalle, comparación, geojson).
- Sugerencias de geocoding para origen/destino.

## Arquitectura

- **Frontend:** React + Vite + React Leaflet.
- **Backend:** FastAPI + OSMnx + NetworkX + utilidades GIS/GeoJSON.
- **Contratos:** definidos en `docs/contracts` y consumidos por frontend sin acoplarse a payloads crudos de proveedores.

Más detalle: `docs/architecture.md`.

## Estructura del repositorio

- `src/`: aplicación frontend (app shell, features, shared, mocks).
- `backend/app/`: API, servicios de dominio, clientes externos, utilidades y schemas.
- `backend/data/`: artefactos de cache/preprocesado para safety/routing/ciclabilidad.
- `docs/`: documentación técnica, contratos y evolución del producto.

## Puesta en marcha local

### 1) Frontend
```bash
npm install
npm run dev
```
Frontend en `http://localhost:5173`.

### 2) Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Backend en `http://localhost:8000`.

> La primera ejecución puede tardar más por warmup de grafo y lectura/generación de cachés.

### 3) Precompute recomendado (muy importante para onboarding)
```bash
cd backend
python -m app.pipelines.build_routing_cache
python -m app.pipelines.build_safety_cache
python -m app.pipelines.build_neighborhood_cyclability
```
Esto deja precalculados los artefactos pesados en `backend/data/` y reduce mucho el tiempo en peticiones reales.  
En routing, el comando `build_routing_cache` genera `edge_metrics_<version>.json` con señales por arista (incluyendo riesgo nocturno) que luego se reutilizan en `fastest/safe/balanced/night` sin recalcular esas señales en cada request.

## Endpoints principales

- `GET /health`
- `GET /api/stations?source=auto|remote|snapshot`
- `GET /api/geocoding/suggest?q=<texto>`
- `GET /api/safety/grid`
- `GET /api/safety/summary`
- `GET /api/cyclability/neighborhoods`
- `GET /api/cyclability/neighborhoods/geojson`
- `GET /api/cyclability/neighborhoods/{id}`
- `GET /api/cyclability/neighborhoods/compare?a=<id>&b=<id>`
- `POST /api/routes`

## Calidad y checks

Frontend:
```bash
npm run lint
npm run build
```

Backend:
```bash
cd backend
pytest
```

## Documentación clave

- Arquitectura: `docs/architecture.md`
- Estado y roadmap unificado: `docs/roadmap.md`
- Contratos API/UI: `docs/contracts/`
- Backend técnico: `backend/README.md`
- Historial por fases (archivo): `docs/slices/`

## Open source

Este repositorio está preparado para colaboración pública. Revisa:
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`
- `LICENSE`
