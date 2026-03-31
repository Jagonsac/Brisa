# Slice 3 — Backend mínimo FastAPI + integración frontend

## Objetivo del slice
Añadir un backend real, pequeño y mantenible para desacoplar Brisa de proveedores externos, manteniendo el contrato de estaciones estable y la demo local robusta.

## Alcance implementado
- Backend `FastAPI` en `backend/` con estructura modular simple.
- Endpoint `GET /health` para chequeo de servicio.
- Endpoint `GET /api/stations` para estaciones Bicimad normalizadas.
- Estrategia de fallback en backend: GBFS -> GeoJSON EMT -> snapshot local.
- Integración frontend configurable por `VITE_API_BASE_URL`.
- Fallback frontend conservado para evitar regresiones en demo si backend no está disponible.
- CORS de desarrollo configurable y sin wildcard.

## Decisiones técnicas
1. **Backend Python + FastAPI + Uvicorn** para ejecución local directa y DX simple.
2. **Separación por capas en backend**:
   - `routers`: endpoints HTTP.
   - `services`: casos de uso de dominio.
   - `clients`: consumo de proveedores externos.
   - `utils`: normalización de payloads externos.
   - `schemas`: contrato tipado de respuestas.
3. **Contrato de estaciones con `data + meta`** para observabilidad sin complicar la API.
4. **Frontend desacoplado de proveedor externo**: el servicio de feature Bicimad prioriza backend y solo usa proveedores directos como fallback de resiliencia local.
5. **Sin sobreingeniería**: no DB, no auth, no colas, no jobs asíncronos externos.

## Estructura del backend
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
├─ .env.example
├─ requirements.txt
└─ README.md
```

## Endpoints creados
### `GET /health`
Respuesta:
```json
{
  "status": "ok",
  "service": "brisa-api",
  "version": "0.1.0",
  "environment": "development"
}
```

### `GET /api/stations?source=auto|remote|snapshot`
- `auto` (default): intenta remoto y cae a snapshot si hace falta.
- `remote`: solo fuentes remotas (GBFS + GeoJSON).
- `snapshot`: fuerza snapshot local.

Respuesta:
```json
{
  "data": [
    {
      "id": "2255",
      "name": "319 - Valdesangil",
      "lat": 40.4684218,
      "lon": -3.7166729,
      "address": "Calle Valdesangil, 34",
      "capacity": 44
    }
  ],
  "meta": {
    "count": 1,
    "source": "gbfs-station-information",
    "fallbackUsed": false,
    "warnings": []
  }
}
```

## Estrategia de fallback
1. Intento `station_information` GBFS.
2. Si falla o viene vacío, intento GeoJSON EMT oficial.
3. Si también falla (o `source=auto`), uso snapshot local de backend.
4. Si no hay ninguna fuente válida, API devuelve `503` con mensaje controlado.

## Integración frontend
- Nueva variable: `VITE_API_BASE_URL`.
- Si está definida, el frontend intenta `GET {VITE_API_BASE_URL}/api/stations`.
- Si backend falla, el frontend mantiene fallback local de Slice 2 para no romper la experiencia.
- UI muestra fuente y si hubo fallback usando `meta.source` y `meta.fallbackUsed`.

## Verificación manual
1. Levantar backend (`uvicorn app.main:app --reload --port 8000`).
2. Probar `http://localhost:8000/health`.
3. Probar `http://localhost:8000/api/stations`.
4. Levantar frontend (`npm run dev`) con `VITE_API_BASE_URL=http://localhost:8000`.
5. Verificar estaciones visibles y tarjeta Bicimad con fuente activa.

## Limitaciones actuales
- Sin persistencia ni cache de backend.
- Sin combinación con `station_status` en tiempo real.
- Sin auth ni perfiles de usuario.
- Sin lógica geoespacial avanzada de rutas/seguridad.

## Preparación para slices siguientes
- La base FastAPI ya permite añadir routers de `routing`, `safety` y `neighborhoods` sin mezclar responsabilidades.
- El contrato `data + meta` deja espacio para trazabilidad de fuentes y métricas operativas.
- La separación cliente/servicio/normalizador facilita sumar proveedores sin romper la UI.
