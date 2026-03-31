# Brisa

Brisa es una aplicación web para ayudar a moverse por Madrid en bicicleta con más seguridad.

## Problema que resuelve
Elegir rutas ciclistas en ciudad suele requerir equilibrio entre rapidez, seguridad y contexto urbano. Brisa busca reducir esa fricción con recomendaciones explicables y datos abiertos.

## Estado actual (Slice 3)
✅ Base React + Vite ejecutable.
✅ UI principal en español con mapa Leaflet de Madrid.
✅ Integración de estaciones Bicimad en mapa.
✅ Backend mínimo FastAPI operativo para desacoplar proveedores externos.
✅ API con `GET /health` y `GET /api/stations`.
✅ CORS de desarrollo configurado y contrato de estaciones documentado.

## Qué incluye Slice 3
- Arquitectura modular frontend + backend.
- Servicio backend de estaciones con estrategia GBFS -> GeoJSON EMT -> snapshot local.
- Frontend configurable por variable `VITE_API_BASE_URL`.
- Fallback frontend mantenido para evitar regresiones de demo.
- Documentación de slice y contratos actualizada.

## Qué NO incluye todavía
- Persistencia real en base de datos.
- Integración operativa de `station_status`.
- Routing real de calles o lógica GIS avanzada.
- Seguridad por usuario, auth o panel de administración.

## Stack tecnológico actual
- Frontend: React + JavaScript (sin TypeScript), Vite, React Leaflet.
- Backend: Python 3.11+, FastAPI, Uvicorn, HTTPX.

## Estructura del proyecto

```text
Brisa/
├─ backend/
│  ├─ app/
│  ├─ .env.example
│  ├─ requirements.txt
│  └─ README.md
├─ docs/
│  ├─ architecture.md
│  ├─ roadmap.md
│  ├─ contracts/
│  └─ slices/
├─ src/
│  ├─ app/
│  ├─ features/
│  ├─ shared/
│  ├─ mocks/
│  ├─ styles/
│  └─ assets/
├─ .env.example
├─ AGENTS.md
├─ README.md
└─ package.json
```

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

## Variables de entorno clave
### Frontend (`/.env`)
- `VITE_API_BASE_URL=http://localhost:8000`

### Backend (`/backend/.env`)
- `PORT=8000`
- `BRISA_ENV=development`
- `BICIMAD_STATIONS_URL=...station_information`
- `BICIMAD_FALLBACK_URL=...bikestationbicimad_geojson.geojson`
- `FRONTEND_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`

## Endpoints disponibles en Slice 3
- `GET /health`
- `GET /api/stations?source=auto|remote|snapshot`

## Verificación manual rápida
1. Levantar backend y comprobar `GET /health`.
2. Probar `GET /api/stations` y verificar `data + meta`.
3. Levantar frontend con `VITE_API_BASE_URL` apuntando al backend.
4. Confirmar estaciones visibles en mapa y estado de fuente/fallback en tarjeta Bicimad.

## Roadmap resumido
- Slice 1: base técnica + UI + mapa + docs ✅
- Slice 2: estaciones Bicimad en mapa ✅
- Slice 3: backend mínimo + API de estaciones ✅
- Slice 4: routing más corto
- Slice 5: score de seguridad + heatmap
- Slice 6: rutas seguras y nocturnas
- Slice 7: índice por barrio + panel
- Slice 8: pulido concurso/portfolio
