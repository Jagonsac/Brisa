# Slice 6.5 — Hardening de routing seguro (edge-first)

## Objetivo
Endurecer el motor multicriterio para que la decisión de ruta segura/nocturna sea **edge-first** y no dependa de una grid gruesa como señal principal.

## Cambios clave
- Filtrado explícito de legalidad ciclista por edge (`bicycle=no`, `access=no`, `motorroad=yes`, `motorway`, `motorway_link`).
- `trunk`/`trunk_link` se bloquean por defecto salvo infraestructura ciclista explícita (ej. `cycleway=track`).
- Nuevo pipeline de métricas por edge cacheadas en `backend/data/routing/edge_metrics_v2.json`.
- El routing usa estas métricas cacheadas para `fastest`, `balanced`, `safe` y `night`.

## Modelo de seguridad edge-first
Cada edge calcula señales independientes y explicables:
- hostilidad vial (clase de vía, carriles, velocidad)
- exposición motorizada (aforos + IMD cuando hay datos)
- accidentalidad general y específica bici (con suavizado Bayesiano)
- complejidad de cruce
- bonus de infraestructura ciclista (tags OSM)
- iluminación y riesgo nocturno

La grid de Slice 5 se mantiene para visualización/fallback, pero no es la señal principal de coste de ruta.

## Datasets integrados en pipeline v2
- Accidentes generales (`300228-34` CSV).
- Accidentes bici (`300110` CSV, con fallback local si falla descarga).
- Aforos no permanentes (`300209-1` CSV).
- Farolas (`300573-0` CSV).
- Aforos peatones/bicicletas (`300321-10` CSV).
- Cruces semaforizados y cruces bici: integración preparada vía CSV configurable (si no hay CSV resoluble, queda fallback neutro).
- IMD: integración preparada con URL configurable (fallback neutro si el recurso no es CSV directo).

## Pesos por modo
- `fastest`: distancia + penalización muy leve solo de hostilidad extrema.
- `balanced`: penalización media de riesgo diurno.
- `safe`: penalización fuerte de riesgo diurno (acepta desvío razonable).
- `night`: base `safe` + penalización fuerte por iluminación/accidentalidad nocturna/tráfico nocturno.

## Preprocesado/caché
Nuevo comando offline:

```bash
cd backend
python -m app.pipelines.build_routing_cache
```

Artefactos:
- `backend/data/routing/edge_metrics_v2.json`
- `backend/data/routing/route_metadata_v2.json`

Runtime:
- carga cachés si existen
- evita recomputar toda la red por request

## Limitaciones reales
- Integraciones SHP (carriles municipales y vías ciclistas oficiales) quedan preparadas para una fase siguiente con stack geoespacial adicional (GeoPandas/Fiona) o export a CSV/GeoJSON estable.
- En ausencia de ciertos recursos CSV oficiales, el pipeline usa fallback neutro y lo deja registrado en metadata.
