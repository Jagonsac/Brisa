# Arquitectura de Brisa

## Arquitectura actual (Slice 3)
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
3. **Servicios de datos**: consumo de API backend (con fallback controlado).
4. **Normalización/contratos**: transformación a modelos internos estables.
5. **Configuración/flags**: toggles de funcionalidades futuras.

### Backend
1. **Routers**: definición de endpoints y códigos HTTP.
2. **Services**: lógica de dominio (estrategia de fuentes y fallback).
3. **Clients**: acceso HTTP a proveedores externos.
4. **Utils**: normalización de formatos externos al contrato Brisa.
5. **Schemas**: contrato de respuesta y validación.
6. **Core**: configuración y CORS.

## Integración Bicimad en Slice 3
- `backend/app/routers/stations.py`: endpoint `GET /api/stations`.
- `backend/app/services/bicimad_service.py`: flujo principal + fallback.
- `backend/app/clients/bicimad_client.py`: cliente HTTP externo.
- `backend/app/utils/station_normalizer.py`: mapeo GBFS/GeoJSON/snapshot -> contrato Brisa.
- `src/features/bicimad/services/bicimadService.js`: consumo backend configurable por `VITE_API_BASE_URL`.

Este diseño mantiene frontend desacoplado de payloads crudos externos y prepara la API para añadir `station_status`, routing y lógica geoespacial en slices siguientes.

## Criterios clave
- Mantener contratos estables entre UI y API.
- Evitar lógica de proveedor en componentes visuales.
- Aumentar funcionalidad por slices sin reestructuras disruptivas.
- Priorizar ejecutabilidad local y claridad sobre complejidad prematura.
