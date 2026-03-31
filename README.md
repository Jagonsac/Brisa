# Brisa

Brisa es una aplicación web para ayudar a moverse por Madrid en bicicleta con más seguridad.

## Problema que resuelve
Elegir rutas ciclistas en ciudad suele requerir equilibrio entre rapidez, seguridad y contexto urbano. Brisa reduce esa fricción con rutas explicables y datos abiertos.

## Estado actual (Slice 4)
✅ Base React + Vite ejecutable.  
✅ UI principal en español con mapa Leaflet de Madrid.  
✅ Integración de estaciones Bicimad en mapa (Slice 2).  
✅ Backend FastAPI con `GET /health` y `GET /api/stations` (Slice 3).  
✅ Routing real más corto con `POST /api/routes` usando OSMnx + Nominatim (Slice 4).  
✅ Ruta dibujada en mapa con resumen mínimo de distancia.

## Qué incluye Slice 4
- Formulario origen/destino conectado a backend.
- Geocoding en backend (Nominatim), no en frontend.
- Carga de red bike de Madrid por OSMnx con caché GraphML.
- Cálculo shortest-path por longitud (`length`).
- Render de ruta GeoJSON, markers de origen/destino y ajuste de bounds en mapa.
- Modos de ruta honestos: solo “Rápida” implementada; resto “Próximamente”.

## Qué NO incluye todavía
- Score de seguridad real (Slice 5).
- Rutas seguras/equilibradas/nocturnas (Slice 6).
- Accidentes, tráfico o barrios en algoritmo de ruta.

## Stack tecnológico actual
- Frontend: React + JavaScript (sin TypeScript), Vite, React Leaflet.
- Backend: Python 3.11+, FastAPI, Uvicorn, HTTPX, OSMnx.

## Cómo ejecutar localmente

### 1) Frontend
```bash
npm install
cp .env.example .env
npm run dev
```
Frontend en `http://localhost:5173`.

### 2) Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```
Backend en `http://localhost:8000`.

> La primera petición a `POST /api/routes` puede tardar más por descarga y guardado inicial del grafo bike de Madrid.

## Variables de entorno clave
### Frontend (`/.env`)
- `VITE_API_BASE_URL=http://localhost:8000`

### Backend (`/backend/.env`)
- `PORT=8000`
- `BRISA_ENV=development`
- `FRONTEND_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`
- `OSMNX_PLACE_QUERY=Madrid, Spain`
- `OSMNX_NETWORK_TYPE=bike`
- `OSMNX_GRAPH_FILENAME=madrid_bike.graphml`
- `NOMINATIM_BASE_URL=https://nominatim.openstreetmap.org/search`
- `NOMINATIM_USER_AGENT=Brisa/0.1 (development)`
- `NOMINATIM_COUNTRY_CODES=es`

## Endpoints disponibles
- `GET /health`
- `GET /api/stations?source=auto|remote|snapshot`
- `POST /api/routes`

## Próximos pasos
- Slice 5: score de seguridad + visualización.
- Slice 6: rutas seguras/equilibradas/nocturnas reales.
