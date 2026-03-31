# Brisa Backend (Slice 4)

Backend FastAPI para desacoplar la app frontend de proveedores externos y resolver routing real ciclista.

## Qué incluye
- `GET /health`: estado del servicio.
- `GET /api/stations`: estaciones Bicimad normalizadas.
- `POST /api/routes`: ruta más corta real entre origen y destino sobre red OSM bike.
- `GET /api/geocoding/suggest`: sugerencias de origen/destino normalizadas para frontend.
- CORS configurable por variable de entorno.
- Caché de grafo OSMnx en disco (`backend/data/graphs/*.graphml`) y en memoria.

## Estructura

```text
backend/
├─ app/
│  ├─ core/
│  ├─ routers/
│  ├─ services/
│  ├─ clients/
│  ├─ schemas/
│  ├─ utils/
│  ├─ data/
│  └─ main.py
├─ data/
│  └─ graphs/
├─ .env.example
└─ requirements.txt
```

## Arranque local

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

> Nota: la primera llamada de rutas puede tardar más porque descarga y guarda el grafo de Madrid.

## Variables de entorno
- `PORT`
- `BRISA_ENV`
- `FRONTEND_ORIGINS`
- `BICIMAD_STATIONS_URL`
- `BICIMAD_FALLBACK_URL`
- `OSMNX_PLACE_QUERY`
- `OSMNX_NETWORK_TYPE`
- `OSMNX_GRAPH_FILENAME`
- `NOMINATIM_BASE_URL`
- `NOMINATIM_USER_AGENT`
- `NOMINATIM_COUNTRY_CODES`

## Endpoints
### `GET /health`
Estado del backend.

### `GET /api/stations?source=auto|remote|snapshot`
Estaciones Bicimad normalizadas.

### `GET /api/geocoding/suggest?q=<texto>`
Devuelve hasta 5 sugerencias geocodificadas en Madrid para autocompletado.

### `POST /api/routes`
Request:

```json
{
  "originQuery": "Atocha",
  "destinationQuery": "Plaza de Castilla",
  "mode": "fastest"
}
```

Respuesta:
- `data.routeGeoJson`: `Feature` GeoJSON con `LineString`.
- `data.origin` y `data.destination`: geocodificación resuelta.
- `data.summary`: distancia en metros y kilómetros.
- `meta`: fuente (`osmnx`) y origen de grafo (`cache|download`).

## Qué NO hace todavía
- Modos `safe`, `balanced` y `night`.
- Score de seguridad y rutas equilibradas/nocturnas.
- Persistencia geoespacial avanzada (PostGIS/Supabase).
