# Slice 8 — Routing multimodal útil con Bicimad

## Objetivo
Integrar Bicimad como opción real de planificación multimodal en `POST /api/routes`, reutilizando el motor de routing existente para el tramo bici y añadiendo tramos peatonales reales.

## Qué se implementa
- Nuevo flag de request: `useBicimad` (compatible también con `transportMode: "bicimad"`).
- Selección de estaciones en dos fases:
  1. preselección espacial por distancia (haversine, radio hasta 1500 m),
  2. evaluación real de pares con `walk + bike + walk`.
- Tramo bici con perfiles existentes `fastest|safe|balanced|night`.
- Tramos andando con grafo `walk` de OSMnx cacheado.
- Uso de `station_information` + `station_status` (TTL corto) y fallback a snapshot/estático cuando falla vivo.
- Respuesta multimodal con `segments`, `stations`, desglose de tiempos/distancias y metadata de fallback.

## Contrato y compatibilidad
- Se mantiene `POST /api/routes`.
- Si `useBicimad=false` (default): flujo actual sin cambios funcionales.
- Si `useBicimad=true`: respuesta extendida con `transportMode: "bicimad"` y segmentos multimodales.

## UX
- Toggle “Usar Bicimad (ruta multimodal)”.
- Estilo de segmentos andando: azul punteado.
- Marcadores dedicados para estación de salida/llegada recomendadas.
- Panel con desglose andar/bici y disponibilidad relevante.

## Limitaciones conocidas
- Heurística inicial configurable pero todavía simple (no usa históricos de fiabilidad).
- El score multimodal aún no compara explícitamente contra “caminar directo” o “bici propia” en esta slice.
- La disponibilidad viva depende del feed GBFS; si falla, se usa fallback sin disponibilidad en tiempo real.
