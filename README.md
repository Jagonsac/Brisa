# Brisa

Brisa es una aplicación web para ayudar a moverse por Madrid en bicicleta con más seguridad.

## Problema que resuelve
Elegir rutas ciclistas en ciudad suele requerir equilibrio entre rapidez, seguridad y contexto urbano. Brisa reduce esa fricción con rutas explicables y datos abiertos.

## Estado actual (Slice 4 corregido)
✅ Base React + Vite ejecutable.  
✅ UI principal en español con mapa Leaflet de Madrid.  
✅ Integración de estaciones Bicimad en mapa (Slice 2).  
✅ Backend FastAPI con `GET /health` y `GET /api/stations` (Slice 3).  
✅ Routing real más corto con `POST /api/routes` usando OSMnx + Nominatim (Slice 4).  
✅ Inputs de origen/destino con sugerencias vía backend (`GET /api/geocoding/suggest`).  
✅ Control para mostrar/ocultar capa Bicimad (oculta por defecto).  
✅ Manejo de errores de ruta en español sin mensaje opaco “Failed to fetch”.

## Qué incluye Slice 4
- Formulario origen/destino conectado a backend.
- Sugerencias de geocoding con debounce (sin llamar Nominatim directo desde frontend).
- Geocoding en backend (Nominatim), no en frontend.
- Carga de red bike de Madrid por OSMnx con caché GraphML.
- Cálculo shortest-path por longitud (`length`).
- Render de ruta GeoJSON, markers de origen/destino y ajuste de bounds en mapa.
- Modos de ruta honestos: solo “Rápida” implementada; resto “Próximamente”.

## Stack tecnológico actual
- Frontend: React + JavaScript (sin TypeScript), Vite, React Leaflet.
- Backend: Python 3.11+, FastAPI, Uvicorn, HTTPX, OSMnx.

## Cómo ejecutar localmente

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

> La primera petición a `POST /api/routes` puede tardar más por descarga y guardado inicial del grafo bike de Madrid.

## Variables de entorno clave
### Frontend (`/.env` opcional)
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
- `GET /api/geocoding/suggest?q=<texto>`

## Verificar el flujo de routing
1. Arranca backend y frontend.
2. Escribe origen/destino (ej. `Plaza de Castilla` y `Matadero Madrid`) y selecciona sugerencias.
3. Deja modo `Rápida` y pulsa “Calcular ruta”.
4. Comprueba que:
   - se dibuja la ruta en el mapa,
   - el mapa se ajusta automáticamente,
   - la tarjeta “Ruta actual” muestra distancia y estado.

## Próximos pasos
- Slice 5: score de seguridad + visualización.
- Slice 6: rutas seguras/equilibradas/nocturnas reales.
