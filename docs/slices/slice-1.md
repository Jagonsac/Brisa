# Slice 1 — Base de Brisa

## Objetivos
- Arrancar proyecto ejecutable desde cero.
- Definir arquitectura modular para crecimiento por slices.
- Mostrar UI profesional mínima y mapa interactivo de Madrid.
- Dejar contratos y documentación de continuidad.

## Decisiones tomadas
- React + JavaScript + Vite para rapidez y claridad.
- CSS Modules para estilos mantenibles.
- React Leaflet para mapa real desde el primer slice.
- Feature flags para controlar evolución incremental.

## Terminado en este slice
- App shell con header, panel lateral y mapa.
- Formulario de origen/destino controlado.
- Selector de modo de ruta (rápida/segura/equilibrada/nocturna).
- Panel de estado del proyecto.
- README, AGENTS, arquitectura, roadmap y contratos base.

## Pendiente para siguientes slices
- Motor real de cálculo de rutas.
- Integración real Bicimad.
- Score de seguridad y barrio.
- Backend FastAPI y endpoints reales.

## Criterios de aceptación
- `npm install` y `npm run dev` levantan app.
- UI en español, limpia y comprensible.
- Mapa funcional centrado en Madrid.
- Documentación suficiente para retomar proyecto sin contexto previo.

## Verificación manual
1. Ejecutar `npm install`.
2. Ejecutar `npm run dev`.
3. Verificar mapa y marcadores demo.
4. Completar origen/destino y pulsar “Preparar ruta”.
5. Cambiar modo de ruta y verificar feedback visual.
