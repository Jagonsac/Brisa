# Slice 7 — Índice de ciclabilidad por barrio

## Objetivo
Convertir la agregación por barrio previa (Slice 5) en una feature completa de producto con índice compuesto, mapa coroplético, ranking, detalle y comparador.

## Qué se reutiliza
- Límites oficiales de barrios (`NeighborhoodService`).
- Métricas edge-first de Slice 6.5 (`edge_metrics_v2`).
- Capa de seguridad y su pipeline cacheado.
- Snapshot de estaciones Bicimad para señal territorial estable.

## Modelo del índice (0..100)
Subscores normalizados con **clipping robusto percentilar (P10-P90)**:
1. `safetyScore` (30%): riesgo diurno + shares de red de bajo/alto riesgo.
2. `bikeInfraScore` (22%): km de infraestructura, densidad km/km², share de red e infraestructura protegida.
3. `lowHostilityScore` (18%): baja exposición a tráfico hostil y arterias.
4. `nightScore` (12%): riesgo nocturno + déficit de iluminación.
5. `junctionScore` (8%): confort por complejidad de cruces.
6. `bicimadScore` (10%): densidad de estaciones + cobertura espacial bufferizada.

Pesos centralizados en `backend/app/core/cyclability_config.py`.

## Pipeline y caché
Comando:

```bash
cd backend
python -m app.pipelines.build_neighborhood_cyclability
```

Artefactos generados:
- `backend/data/cyclability/neighborhoods_scores.json`
- `backend/data/cyclability/neighborhoods_scores.geojson`
- `backend/data/cyclability/metadata.json`

Runtime carga estos artefactos y evita recomputar joins espaciales pesados por request.

## Endpoints
- `GET /api/cyclability/neighborhoods`
- `GET /api/cyclability/neighborhoods/geojson`
- `GET /api/cyclability/neighborhoods/{neighborhood_id}`
- `GET /api/cyclability/neighborhoods/compare?left=...&right=...`

## Explicabilidad
Cada barrio incluye:
- fortalezas y debilidades (reglas deterministas por top/bottom subscores)
- resumen breve en español
- métricas base (km red, share hostil, densidades, cobertura Bicimad)

## Limitaciones reales
- La señal Bicimad usa snapshot estático si no se integra una capa más completa de estaciones.
- Algunas proxies de infraestructura dependen de tags OSM y no sustituyen una auditoría oficial tramo a tramo.
