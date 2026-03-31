# Arquitectura de Brisa

## Arquitectura actual (Slice 4)
Brisa usa una arquitectura modular con frontend React + backend FastAPI:

- `src/app/`: app shell, layout y entrada visual.
- `src/features/`: módulos funcionales de producto.
- `src/shared/`: configuración y recursos reutilizables.
- `src/mocks/`: datos simulados alineados con contratos.
- `backend/app/`: API HTTP, servicios de dominio y adaptadores de proveedor.
- `docs/`: decisiones, roadmap y contratos.

## Separación por capas
### Frontend
1. **Presentación**: componentes de UI y estilos (CSS Modules).
2. **Estado local de feature**: formularios y estado de carga de capas.
3. **Servicios de datos**: consumo de API backend.
4. **Contratos**: frontend consume respuestas estables (`data` + `meta`) del backend.
5. **Configuración/flags**: toggles para activar valor incremental.

### Backend
1. **Routers**: definición de endpoints y códigos HTTP.
2. **Services**: lógica de dominio (geocoding, grafo, shortest-path).
3. **Clients**: acceso HTTP a proveedores externos.
4. **Utils**: serialización GeoJSON y normalizadores.
5. **Schemas**: contratos request/response.
6. **Core**: configuración y CORS.

## Slice 4: flujo de routing real
- `backend/app/routers/routes.py`: endpoint `POST /api/routes`.
- `backend/app/services/geocoding_service.py`: geocoding Nominatim.
- `backend/app/services/graph_service.py`: carga/caché de grafo bike de Madrid.
- `backend/app/services/route_service.py`: snapping + shortest-path + resumen.
- `src/features/routing/services/routesService.js`: consumo de API de rutas.
- `src/features/map/components/MapView.jsx`: pintado GeoJSON y ajuste de mapa.

## Criterios clave
- Contratos estables entre frontend y backend.
- Lógica GIS en backend, no en React.
- Routers finos + servicios dedicados.
- Escalabilidad por slices sin refactorizaciones grandes.
