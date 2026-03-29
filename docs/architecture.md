# Arquitectura de Brisa

## Arquitectura actual (Slice 1)
Brisa usa una arquitectura frontend modular en React:

- `app/`: app shell, layout y punto de entrada visual.
- `features/`: módulos funcionales de producto.
- `shared/`: configuración y recursos reutilizables.
- `mocks/`: datos simulados alineados con contratos.
- `docs/`: decisiones, roadmap y contratos.

## Separación por capas
1. **Presentación**: componentes de UI y estilos (CSS Modules).
2. **Estado local de feature**: formularios, selección de modo de ruta.
3. **Configuración/flags**: toggles de funcionalidades futuras.
4. **Contratos de integración**: JSON y documentación en `docs/contracts`.

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
- `bicimad` consumirá `stations.contract.json` para capas de estaciones.
- `neighborhoods` usará `neighborhood-score.contract.json` para paneles y mapa.
- `safety` añadirá explicaciones sobre segmentos y puntos negros.

## Criterios clave
- Mantener frontend desacoplado de detalles internos del backend.
- Activar nuevas capacidades con feature flags, no con ramas de código ocultas.
- Cada slice debe dejar el sistema más claro, no más complejo.
