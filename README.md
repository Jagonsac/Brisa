# Brisa

Brisa es una aplicación web para planificar rutas ciclistas en Madrid con foco en seguridad y explicabilidad.

## Estado actual (Slice 6)
✅ Frontend React + Vite con mapa Leaflet y UX en español.  
✅ Backend FastAPI con geocoding, routing real y capa de seguridad.  
✅ Modos de ruta operativos en producción local:
- **Rápida** (`fastest`)
- **Segura** (`safe`)
- **Equilibrada** (`balanced`)
- **Nocturna** (`night`)  
✅ Explicaciones deterministas por ruta (sin IA generativa).  
✅ Capa de seguridad Slice 5 intacta y reutilizada para routing.

## Qué añade Slice 6
- Costes multicriterio por edge sobre grafo OSMnx.
- Reutilización del grid de seguridad Slice 5 para `safe/balanced/night`.
- Proxy nocturna con dos capas:
  - iluminación por densidad de farolas
  - accidentalidad ciclista en franja nocturna (22:00–06:00)
- Caché local de atributos preprocesados para acelerar peticiones sucesivas.

## Dataset nuevo en Slice 6
- **Farolas (Unidades luminosas, Ayuntamiento de Madrid)**
  - Se usa como proxy de iluminación nocturna por celda.
  - No se hace fotometría avanzada; solo densidad/cobertura razonable.

## Stack
- Frontend: React + JavaScript (sin TypeScript), Vite, React Leaflet.
- Backend: FastAPI, OSMnx, NetworkX, pyproj.

## Cómo ejecutar

### Frontend
```bash
npm install
npm run dev
```
Frontend: `http://localhost:5173`

### Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Backend: `http://localhost:8000`

> La primera petición de rutas puede tardar más por la generación de cachés en `backend/data/routing` y `backend/data/safety/processed`.

## Endpoints
- `GET /health`
- `GET /api/stations?source=auto|remote|snapshot`
- `GET /api/geocoding/suggest?q=<texto>`
- `GET /api/safety/grid`
- `GET /api/safety/summary`
- `POST /api/routes`

## Prueba manual recomendada (Slice 6)
1. Selecciona origen y destino con sugerencias.
2. Calcula la ruta en los cuatro modos.
3. Comprueba que cambian distancia/recorrido.
4. Revisa en la tarjeta las explicaciones y métricas compactas.
5. Activa capa de seguridad y verifica que la ruta sigue visible.

## Próximos pasos
- Slice 7: mejorar comparativa entre modos y análisis de trade-offs por tramo.
- Slice 8: integración avanzada de infraestructura ciclista y métricas urbanas adicionales.
