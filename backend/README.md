# Brisa Backend (Slice 3)

Backend mínimo en FastAPI para desacoplar la app frontend de las fuentes externas de Bicimad.

## Qué incluye
- `GET /health`: estado del servicio.
- `GET /api/stations`: estaciones Bicimad normalizadas al contrato interno de Brisa.
- CORS de desarrollo configurable por variable de entorno.
- Estrategia de carga: GBFS remoto -> GeoJSON oficial EMT -> snapshot local.

## Estructura

```text
backend/
├─ app/
│  ├─ core/       # configuración y CORS
│  ├─ routers/    # endpoints HTTP
│  ├─ services/   # lógica de negocio del dominio
│  ├─ clients/    # clientes de proveedores externos
│  ├─ schemas/    # modelos de request/response
│  ├─ utils/      # normalizadores y utilidades
│  ├─ data/       # snapshot local para fallback
│  └─ main.py     # bootstrap FastAPI
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

## Variables de entorno
- `PORT`: puerto del backend (por defecto 8000).
- `BRISA_ENV`: entorno (`development`, `staging`, `production`).
- `BICIMAD_STATIONS_URL`: URL principal GBFS.
- `BICIMAD_FALLBACK_URL`: URL fallback oficial EMT.
- `FRONTEND_ORIGINS`: orígenes permitidos separados por coma.

## Endpoints
### GET /health
Respuesta:

```json
{
  "status": "ok",
  "service": "brisa-api",
  "version": "0.1.0",
  "environment": "development"
}
```

### GET /api/stations?source=auto|remote|snapshot
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

## Qué NO hace todavía
- Persistencia en base de datos.
- Integración de `station_status`.
- Autenticación o permisos.
- Rutas ciclistas ni lógica geoespacial avanzada.
