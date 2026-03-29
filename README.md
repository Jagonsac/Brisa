# Brisa

Brisa es una aplicación web para ayudar a moverse por Madrid en bicicleta con más seguridad.

## Problema que resuelve
Elegir rutas ciclistas en ciudad suele requerir equilibrio entre rapidez, seguridad y contexto urbano. Brisa busca reducir esa fricción con recomendaciones explicables y datos abiertos.

## Estado actual (Slice 1)
✅ Base React + Vite ejecutable.
✅ UI principal en español con layout profesional.
✅ Mapa interactivo Leaflet centrado en Madrid.
✅ Formulario de origen/destino y selector visual de modo de ruta.
✅ Panel de estado del proyecto y documentación completa.
✅ Estructura preparada para crecer por slices.

## Qué incluye Slice 1
- Arquitectura frontend modular por capas (`app`, `features`, `shared`, `mocks`).
- Sistema de feature flags activo desde el inicio.
- Contratos iniciales frontend-backend en `docs/contracts`.
- Roadmap documentado de slices futuros.

## Qué NO incluye todavía
- Backend real ni persistencia.
- Cálculo de rutas reales.
- Integración real con Bicimad.
- Scores de seguridad o barrio en producción.

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

## Roadmap resumido
- Slice 1: base técnica + UI + mapa + docs
- Slice 2: estaciones Bicimad en mapa
- Slice 3: backend mínimo + endpoint de salud
- Slice 4: routing más corto
- Slice 5: score de seguridad + heatmap
- Slice 6: rutas seguras y nocturnas
- Slice 7: índice por barrio + panel
- Slice 8: pulido concurso/portfolio

## Qué hace cada feature principal
- `map`: render de mapa y capa visual inicial.
- `search`: formulario y modos de ruta.
- `projectStatus`: estado del producto y narrativa actual.
- `routing`, `safety`, `nightMode`, `bicimad`, `neighborhoods`: placeholders documentados para slices futuros.

## Cómo retomar el proyecto sin perderse
1. Leer `docs/slices/slice-1.md` y `docs/roadmap.md`.
2. Revisar `docs/contracts` antes de integrar APIs.
3. Encender una feature solo mediante `featureFlags`.
4. Implementar cambios dentro de la feature correspondiente.

## Reglas de limpieza y convenciones
- Componentes pequeños, una responsabilidad clara.
- Evitar lógica de negocio compleja en capas visuales.
- Mocks y configuración fuera de componentes.
- Nombres explícitos: `FeatureNameThing.jsx`, `Thing.module.css`.

## Qué carpetas tocar según necesidad
- UI global: `src/app` y `src/styles`
- Feature concreta: `src/features/<feature>`
- Config compartida: `src/shared/config` y `src/shared/constants`
- Datos simulados: `src/mocks`
- Contratos/documentación: `docs/contracts` y `docs/slices`

## Archivos que no conviene tocar salvo necesidad
- `docs/contracts/*.json` (son base de integración futura)
- `src/shared/config/featureFlags.js` (cambiar con criterio de slice)

## Cómo añadir un nuevo slice sin romper la estructura
1. Crear `docs/slices/slice-X.md`.
2. Activar o añadir feature flags necesarias.
3. Implementar solo una vertical funcional.
4. Actualizar `roadmap.md` y el panel de estado.
5. Verificar demo visible antes de cerrar el slice.

## Decisiones de arquitectura
- Frontend desacoplado por contratos JSON para facilitar backend evolutivo.
- Feature flags para controlar avance progresivo y demos estables.
- Modularidad por features para vibecodear sin deuda estructural.

## Cómo trabajar con agentes de IA
- Leer primero `AGENTS.md`.
- No mezclar cambios de varios slices en un mismo commit.
- Documentar decisiones y actualizar contratos antes de integrar APIs.

## Siguientes pasos recomendados
1. Slice 2: capa de estaciones Bicimad (mock + contrato + render en mapa).
2. Slice 3: levantar backend FastAPI mínimo con endpoints simulados.
3. Empezar integración frontend-backend manteniendo contratos estables.
