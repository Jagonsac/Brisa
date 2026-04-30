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
1. `safetyScore` (28%): riesgo diurno + shares de red de bajo/alto riesgo + accidentalidad ciclista relativa a exposición aproximada.
2. `bikeInfraScore` (20%): km de infraestructura, share de red e infraestructura protegida, corrigiendo sesgo por área con densidad sobre área servida por red ciclable.
3. `lowHostilityScore` (16%): baja exposición a tráfico hostil y arterias.
4. `greenCyclableScore` (12%): red ciclable legal en entorno verde (sin bonus por hectárea verde bruta).
5. `nightScore` (12%): riesgo nocturno + déficit de iluminación.
6. `junctionScore` (8%): confort por complejidad de cruces.
7. `bicimadScore` (4%): densidad de estaciones + cobertura espacial bufferizada, reduciendo el castigo de zonas recreativas.

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
- nuevas métricas trazables de calibración: `servedAreaRatio`, `infraDensityKmPerServedKm2`, `bikeAccidentRelative`, `greenCyclableShare` y `greenCyclableQuality`.

## Decisiones de calibración (sesgo de Casa de Campo)
- Se evita premiar “verde ciego”: `greenCyclableScore` solo sube cuando hay red **ciclable legal** y con calidad razonable dentro de entorno verde.
- Se reduce sesgo de barrios grandes con componente no urbana al usar `infraDensityKmPerServedKm2` junto a la densidad clásica por km² total.
- La accidentalidad mantiene suavizado bayesiano del edge-level y se corrige por exposición ciclista aproximada (`bikePresenceScore` con fallback estable) para aproximar riesgo por uso.

### Rebalanceo específico de parques ciclables (PCR)
- Se añade un guardrail de **perfil parque** para barrios con red ciclable verde intensa y hostilidad baja:
  - `greenCyclableShare >= 0.45`
  - `hostileShare <= 0.20`
  - `networkKm >= 15`
  - `bikeAccidentRelative <= 0.85`
  - subscore mínimo en `greenCyclableScore`, `lowHostilityScore` y `safetyScore`.
- Si el barrio pasa el gating, se recalcula un score alternativo con pesos park-profile (más peso en `greenCyclable` y `lowHostility`, menos en `bikeInfra` y `bicimad`) y se aplica un floor condicionado (`60` o `70`) según calidad conjunta verde/hostilidad.
- El payload expone trazabilidad mediante `rebalancing.applied/profile/boost/reasons`, permitiendo auditar cuándo el ajuste entró en juego.

### Nota de calibración (antes/después)
- **Casa de Campo**: mejora esperada en `bikeInfraScore` y `greenCyclableScore`; deja de quedar artificialmente en cola por baja densidad territorial bruta y baja presencia Bicimad.
- **Sol (control urbano denso)**: se mantiene alto en infraestructura/servicio, sin saltos abruptos en ranking.
- **El Pardo (control gran superficie no urbana)**: mejora moderada, limitada por cobertura ciclable legal efectiva (sin premio por área verde no ciclable).

> Referencia de validación: regenerar caché con `python -m app.pipelines.build_neighborhood_cyclability` y comparar top/bottom antes/después para estos tres barrios.

## Limitaciones reales
- La señal Bicimad usa snapshot estático si no se integra una capa más completa de estaciones.
- Algunas proxies de infraestructura dependen de tags OSM y no sustituyen una auditoría oficial tramo a tramo.
