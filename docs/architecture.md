# Arquitectura de Brisa

## Arquitectura actual (Slice 2)
Brisa usa una arquitectura frontend modular en React:

- `app/`: app shell, layout y punto de entrada visual.
- `features/`: módulos funcionales de producto.
- `shared/`: configuración y recursos reutilizables.
- `mocks/`: datos simulados alineados con contratos.
- `docs/`: decisiones, roadmap y contratos.

## Separación por capas
1. **Presentación**: componentes de UI y estilos (CSS Modules).
2. **Estado local de feature**: formularios y estado de carga de capas.
3. **Servicios de datos**: acceso a proveedores externos (GBFS/GeoJSON) aislado por feature.
4. **Normalización/contratos**: transformación a modelos internos estables.
5. **Configuración/flags**: toggles de funcionalidades futuras.

## Integración Bicimad en Slice 2
- `src/features/bicimad/services`: estrategia de fuente principal y fallback.
- `src/features/bicimad/utils`: normalización de payloads externos.
- `src/features/bicimad/hooks`: carga encapsulada para UI (`loading`, `error`, `source`, `usedFallback`).
- `src/features/bicimad/components`: capa de mapa y tarjeta de estado, sin lógica de fetch.

Este diseño mantiene el mapa desacoplado de los formatos GBFS/GeoJSON y preparado para combinar `station_information` + `station_status` en slices siguientes.

## Por qué React + Vite
- Inicio rápido y ejecutabilidad inmediata.
- Ecosistema maduro para map rendering y componentes.
- Build ágil y DX excelente para iteraciones por slices.

## Stack futuro recomendado
- **Backend**: FastAPI (Python) para endpoints de rutas, seguridad y explicabilidad.
- **Datos**: Supabase con Postgres + PostGIS para operaciones geoespaciales.

## Conexión futura entre módulos
- `search` emite solicitudes de ruta siguiendo `route-request.contract.json`.
- `routing` consume respuesta normalizada de `route-response.contract.json`.
- `bicimad` ya consume `stations.contract.json` y queda listo para unir estado en tiempo real.
- `neighborhoods` usará `neighborhood-score.contract.json` para paneles y mapa.
- `safety` añadirá explicaciones sobre segmentos y puntos negros.

## Criterios clave
- Mantener frontend desacoplado de detalles internos del backend.
- Activar nuevas capacidades con feature flags, no con ramas de código ocultas.
- Cada slice debe dejar el sistema más claro, no más complejo.
