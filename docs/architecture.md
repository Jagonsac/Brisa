# Arquitectura de Brisa

## Resumen

Brisa sigue una arquitectura modular orientada a dominio, separando claramente:
- **Interfaz y experiencia de usuario** (frontend React).
- **Lógica geoespacial y de decisión** (backend FastAPI).
- **Contratos de datos** (documentados en `docs/contracts`).

Principio clave: la lógica GIS y de scoring vive en backend; el frontend renderiza, orquesta interacción y muestra explicaciones.

## Capas del frontend (`src/`)

1. **`app/`**: shell principal, layout y punto de entrada.
2. **`features/`**: módulos funcionales aislados (`routing`, `search`, `safety`, `bicimad`, `neighborhoods`, etc.).
3. **`shared/`**: constantes, hooks y utilidades transversales.
4. **`mocks/`**: snapshots y datos de apoyo para UX/demo local.

Reglas:
- No incluir geoprocesado complejo en componentes React.
- Consumir siempre contratos internos estables.
- Mantener componentes visuales ligeros y lógica en servicios/hooks.

## Capas del backend (`backend/app/`)

1. **Routers (`routers/`)**: endpoints HTTP finos, validación inicial y códigos de error.
2. **Services (`services/`)**: reglas de negocio (routing, seguridad, ciclabilidad, multimodal).
3. **Clients (`clients/`)**: acceso a proveedores externos (ej. Bicimad).
4. **Schemas (`schemas/`)**: request/response tipados para contratos estables.
5. **Utils (`utils/`)**: parseo/normalización/serialización reutilizable.
6. **Core (`core/`)**: configuración, perfiles y CORS.
7. **Pipelines (`pipelines/`)**: precomputes/caches para rendimiento offline y arranque estable.

## Dominios funcionales

- **Routing multicriterio:** rutas `fastest`, `safe`, `balanced`, `night`.
- **Multimodal Bicimad:** decisión de estaciones y segmentos `walk + bike + walk`.
- **Safety layer:** grid y resumen de seguridad para visualización y explicabilidad.
- **Cyclability neighborhoods:** score por barrio, detalle y comparación.
- **Geocoding:** sugerencias de ubicación para origen/destino.

## Flujo de una petición de rutas

1. Frontend envía `POST /api/routes` con origen, destino, modo y flags.
2. Router normaliza payload y delega en `RouteService`.
3. Servicio resuelve geocoding/snapping sobre grafo y calcula mejor ruta según perfil.
4. Se agregan métricas/explicaciones deterministas.
5. Frontend recibe GeoJSON + resumen y renderiza en mapa/panel.

## Rendimiento y datos

- Uso de cache/preprocesado para reducir recomputación en requests.
- Warmup del motor de rutas durante el lifespan de FastAPI.
- Artefactos persistidos en `backend/data/` para routing/safety/cyclability.

## Decisiones de diseño

- Backend-first para cálculos geoespaciales.
- Contratos de integración como frontera explícita.
- Evolución incremental por capacidades, preservando compatibilidad.

