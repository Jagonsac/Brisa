# Roadmap de Brisa

## Slice 1 — Base + mapa + UI + docs (completado)
- Base React/Vite
- Mapa Leaflet en Madrid
- Formulario origen/destino + modo de ruta
- Estado del proyecto
- Contratos y documentación inicial

## Slice 2 — Estaciones Bicimad en mapa (completado)
- Capa de estaciones Bicimad en mapa
- Carga real desde GBFS `station_information`
- Fallback oficial EMT + snapshot local
- Normalización a contrato interno estable
- Estados de carga/error/fallback en UI

## Slice 3 — Backend mínimo (completado)
- FastAPI inicial en `backend/`
- Endpoint de salud `GET /health`
- Endpoint de estaciones `GET /api/stations`
- Normalización y fallback en backend
- Integración frontend configurable por `VITE_API_BASE_URL`

## Slice 4 — Routing más corto (completado)
- Endpoint `POST /api/routes`
- Geocoding backend con Nominatim
- Grafo bike de Madrid cacheado (OSMnx GraphML)
- Cálculo shortest-path por `length`
- Pintado de ruta real en mapa + resumen de distancia

## Slice 5 — Score de seguridad + heatmap (completado)
- Grid de seguridad ciclista v1 por celdas
- API `GET /api/safety/grid` y `GET /api/safety/summary`
- Visualización choropleth con leyenda y popups

## Slice 6 — Rutas seguras y nocturnas (completado)
- Perfil seguro y nocturno
- Reglas para horario/luz y vías preferentes

## Slice 7 — Índice por barrio + panel (completado)
- Score de ciclabilidad por barrio
- Panel comparativo y visualizaciones

## Slice 8 — Routing multimodal Bicimad (completado)
- Opción real “Usar Bicimad” sobre perfiles existentes fastest/safe/balanced/night
- Ruta en tres tramos: walk + bike + walk
- Selección de estaciones por score de viaje completo (no solo cercanía)
- GBFS `station_information` + `station_status` con fallback estable
- Visualización multimodal y desglose por segmentos en UI
