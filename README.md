# Brisa

Brisa es una aplicación web para ayudar a moverse por Madrid en bicicleta con más seguridad.

## Problema que resuelve
Elegir rutas ciclistas en ciudad suele requerir equilibrio entre rapidez, seguridad y contexto urbano. Brisa busca reducir esa fricción con recomendaciones explicables y datos abiertos.

## Estado actual (Slice 2)
✅ Base React + Vite ejecutable.
✅ UI principal en español con layout profesional.
✅ Mapa interactivo Leaflet centrado en Madrid.
✅ Formulario de origen/destino y selector visual de modo de ruta.
✅ Integración de estaciones Bicimad en mapa con popups mínimos.
✅ Carga real de estaciones desde GBFS con fallback oficial + snapshot local.
✅ Panel de estado del proyecto y documentación de contratos actualizada.

## Qué incluye Slice 2
- Arquitectura frontend modular por capas (`app`, `features`, `shared`, `mocks`).
- Sistema de feature flags (`enableBicimad`, `enableBicimadStationsLayer`).
- Servicio de datos Bicimad con timeout y degradación elegante.
- Hook de carga de estaciones con estados de UX (`loading`, `error`, `fallback`, `sin datos`).
- Contrato interno estable en `docs/contracts/stations.contract.json`.

## Qué NO incluye todavía
- Backend real ni persistencia.
- Cálculo de rutas reales.
- Integración operativa de `station_status` (solo preparación estructural).
- Recomendación de estaciones o predicción de disponibilidad.

## Stack tecnológico actual
- React + JavaScript (sin TypeScript)
- Vite
- React Leaflet + Leaflet
- CSS Modules + CSS global limpio
- ESLint (flat config)

## Stack previsto para fases futuras
- Backend: Python + FastAPI
- Datos/geo: Supabase (Postgres + PostGIS)

## Estructura del proyecto

```text
Brisa/
├─ docs/
│  ├─ architecture.md
│  ├─ roadmap.md
│  ├─ contracts/
│  └─ slices/
├─ public/
├─ src/
│  ├─ app/
│  ├─ features/
│  ├─ shared/
│  ├─ mocks/
│  ├─ styles/
│  └─ assets/
├─ AGENTS.md
├─ README.md
└─ package.json
```

## Filosofía de trabajo por slices
Cada slice debe ser una vertical pequeña, visible y usable. Se prioriza entregar valor real incremental, sin mezclar demasiados objetivos en una sola iteración.

## Cómo ejecutar localmente
1. `npm install`
2. `npm run dev`
3. Abrir la URL indicada por Vite (normalmente `http://localhost:5173`).

Comandos extra:
- `npm run lint`
- `npm run build`
- `npm run preview`

## Verificación manual de Slice 2
1. Iniciar la app con `npm run dev`.
2. Verificar que el mapa de Madrid se muestra con normalidad.
3. Confirmar puntos Bicimad en el mapa (círculos azules).
4. Pulsar una estación y revisar popup (`nombre`, `dirección`, `capacidad`).
5. Revisar panel Bicimad en sidebar para estado/fuente/fallback.

## Fuente de datos de estaciones
1. Fuente principal: GBFS `station_information`.
2. Fallback oficial: GeoJSON EMT Madrid.
3. Fallback local: snapshot en `src/mocks/bicimadStationsSnapshot.js`.

Esta estrategia permite demos estables incluso ante problemas de red o CORS.

## Roadmap resumido
- Slice 1: base técnica + UI + mapa + docs ✅
- Slice 2: estaciones Bicimad en mapa ✅
- Slice 3: backend mínimo + endpoint de salud
- Slice 4: routing más corto
- Slice 5: score de seguridad + heatmap
- Slice 6: rutas seguras y nocturnas
- Slice 7: índice por barrio + panel
- Slice 8: pulido concurso/portfolio

## Qué hace cada feature principal
- `map`: render de mapa y capas visuales.
- `search`: formulario y modos de ruta.
- `projectStatus`: estado del producto y narrativa actual.
- `bicimad`: carga/normalización/render de estaciones.
- `routing`, `safety`, `nightMode`, `neighborhoods`: evolución por slices futuros.

## Cómo retomar el proyecto sin perderse
1. Leer `docs/slices/slice-2.md` y `docs/roadmap.md`.
2. Revisar `docs/contracts` antes de integrar APIs.
3. Encender/apagar features solo mediante `featureFlags`.
4. Implementar cambios dentro de la feature correspondiente.
