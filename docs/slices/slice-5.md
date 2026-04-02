# Slice 5 — Capa de seguridad ciclista v1 (grid + choropleth)

## Objetivo
Entregar una primera superficie de seguridad ciclista para Madrid, visible en el mapa y explicable, sin modificar todavía el algoritmo de routing rápido.

## Qué se implementa en esta slice
- Backend FastAPI con dos endpoints nuevos:
  - `GET /api/safety/grid`
  - `GET /api/safety/summary`
- `GET /api/safety/grid` soporta agregación por `aggregation=neighborhood` (default) para visualización, y `aggregation=cell` para detalle técnico.
- Pipeline de construcción de grid por celdas cuadradas (250m configurable).
- Score v1 de seguridad `0..100` por celda.
- Mapeo del score del grid a polígonos de barrio de Madrid para choropleth más legible.
- Caché local del preprocesado en `backend/data/safety/processed`.
- Capa visual choropleth en frontend con toggle, popup y leyenda.

## Fuentes de datos usadas
1. **Accidentes con implicación de bicicletas (Madrid, 2024)** como núcleo del riesgo observado.
2. **Aforos permanentes** como enriquecimiento de exposición al tráfico con adapter degradable.
3. **OSM/OSMnx** para contexto vial y proxy de infraestructura ciclista.

## Decisión de modelado (explicable)
Se usa un grid cuadrado en CRS proyectado (`EPSG:25830`) para medir exposición por área.

### Componentes por celda
- `weightedBikeAccidents`
- `trafficExposure`
- `hostileRoadExposure`
- `bikeInfraScore`

### Fórmula v1
`riskRaw = 0.50*accidents + 0.20*traffic + 0.20*hostileRoads - 0.10*bikeInfra`

Cada componente se normaliza por percentiles (clipping robusto), luego se transforma a:

`safetyScore = round(100 * (1 - normalizedRisk))`

## Accidentes: decisiones clave
- Se descartan registros sin coordenadas UTM válidas.
- Conversión `EPSG:25830 -> EPSG:4326` documentada en config.
- Deduplicación por `num_expediente + fecha + hora + coordenadas` para evitar sobrerrepresentación por persona implicada.
- Se conserva la severidad máxima observada en cada accidente deduplicado.

## Tráfico: estrategia pragmática
- Se intenta combinar estaciones permanentes con dataset mensual de intensidad.
- Si el matching/campo de intensidad mensual no es robusto, se activa **fallback** (intensidad base por estación).
- El fallback no bloquea la capa: el score sigue siendo útil con accidentes + contexto vial + bike infra.

## Infraestructura y contexto vial OSM
- Hostile classes: `trunk`, `primary`, `secondary` y links.
- Bike-friendly: `highway=cycleway`, presencia de `cycleway`, vías residenciales y calmadas.
- Métrica por celda basada en proporción de longitud de aristas.

## Caché y rendimiento
Directorio:
- `backend/data/safety/raw/` (descargas de trabajo)
- `backend/data/safety/processed/madrid_safety_grid_v1.geojson`
- `backend/data/safety/processed/safety_metadata_v1.json`
- `backend/data/safety/processed/madrid_safety_neighborhood_grid_v2.geojson`
- `backend/data/safety/processed/safety_neighborhood_metadata_v2.json`

Regla:
- Si existe caché procesada, se sirve inmediatamente.
- Si no existe, se construye en modo lazy en la primera petición.

## Limitaciones conocidas
- El recurso mensual de aforos puede cambiar estructura/campos y forzar fallback parcial.
- La severidad de accidentes usa un mapping simple inicial (recalibrable).
- Esta slice no modifica todavía `POST /api/routes`.
- La agregación barrio-celda usa asignación por centroide de celda (con fallback por proximidad) en CRS proyectado (EPSG:25830) para reducir de forma drástica el tiempo de cómputo y mejorar la carga inicial del heatmap.
- La carga de barrios prioriza el dataset local versionado `backend/data/safety/raw/madrid_barrios_131.geojson`, manteniendo fallback remoto + caché si faltase ese recurso.

## Criterios de aceptación de Slice 5
- API de safety operativa (`grid` + `summary`).
- Capa visual activable/desactivable en frontend.
- Popups con score, accidentes y explicación.
- Ruta rápida de Slice 4 sigue funcionando sin cambios de contrato.
- Documentación y contratos actualizados.

## Verificación manual
1. Arrancar backend y frontend.
2. Abrir la app y activar “Mostrar capa de seguridad ciclista v1”.
3. Verificar leyenda, colores y popups por celda.
4. Calcular una ruta rápida y confirmar que se dibuja sobre la capa.
5. Consultar:
   - `GET /api/safety/grid`
   - `GET /api/safety/summary`
