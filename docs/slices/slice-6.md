# Slice 6 — Routing multicriterio real (rápida / segura / equilibrada / nocturna)

## Objetivo
Extender `POST /api/routes` para soportar cuatro modos reales de cálculo (`fastest`, `safe`, `balanced`, `night`) reutilizando el grid de seguridad del Slice 5 y añadiendo dos capas nuevas para el modo nocturno:
- proxy de iluminación urbana (farolas)
- riesgo nocturno por accidentalidad ciclista

## Reutilización de Slice 5
- Se reutiliza la malla de seguridad en `backend/data/safety/processed/madrid_safety_grid_v1.geojson`.
- El coste por seguridad para `safe` y `balanced` usa el `riskScore` normalizado por edge (0..1).
- La capa visual de seguridad y su resumen en frontend no se tocan; siguen siendo independientes del motor de routing.

## Novedades del Slice 6
- Nuevo servicio de pesos de edge con caché: `backend/app/services/edge_weight_service.py`.
- Nuevo servicio de iluminación: `backend/app/services/lighting_service.py`.
- Nuevo servicio de riesgo nocturno: `backend/app/services/night_risk_service.py`.
- `RouteService` ahora calcula rutas para los cuatro modos y devuelve explicaciones deterministas.
- UI actualizada para habilitar los cuatro modos y mostrar métricas compactas + explicaciones.

## Dataset nuevo usado
### Farolas (alumbrado público)
- Dataset: Unidades luminosas (farolas) de Madrid.
- Uso: proxy simple de iluminación por celda (densidad de farolas).
- Campo espacial: `X_UTM`, `Y_UTM` (EPSG:25830).

## Construcción del modo nocturno
1. **Lighting grid**: cuenta de farolas por celda (malla de 250m). Normalización min-max para `lightingScore` y derivación `lightingDeficit = 1 - lightingScore`.
2. **Night risk grid**: accidentes bici filtrados por franja nocturna (`22:00` a `06:00`) agregados por celda y normalizados.
3. **Coste night por edge**: promedio por muestreo (inicio/mitad/fin de cada edge) sobre:
   - `safetyRiskNormalized`
   - `lightingDeficitNormalized`
   - `nightRiskNormalized`

## Fórmulas de peso por modo
- `fastest`: `length`
- `safe`: `length * (1 + SAFE_RISK_MULTIPLIER * safetyRiskNormalized)`
- `balanced`: `length * (1 + BALANCED_RISK_MULTIPLIER * safetyRiskNormalized)`
- `night`: `length * (1 + NIGHT_BASE_RISK_MULTIPLIER * safetyRiskNormalized + NIGHT_LIGHTING_MULTIPLIER * lightingDeficitNormalized + NIGHT_ACCIDENT_MULTIPLIER * nightRiskNormalized)`

Pesos v1 configurados (env, con defaults):
- `SAFE_RISK_MULTIPLIER=2.5`
- `BALANCED_RISK_MULTIPLIER=1.1`
- `NIGHT_BASE_RISK_MULTIPLIER=1.2`
- `NIGHT_LIGHTING_MULTIPLIER=1.0`
- `NIGHT_ACCIDENT_MULTIPLIER=0.8`
- `NIGHT_START_HOUR=22`
- `NIGHT_END_HOUR=6`

## Estrategia de caché
Se implementa caché lazy en `backend/data/routing/`:
- `edge_weights_v1.json` (métricas de seguridad/iluminación/riesgo nocturno por edge)
- `lighting_grid_v1.geojson` + metadatos
- `night_risk_grid_v1.geojson` + metadatos
- `route_metadata_v1.json` (pesos finales y fallback usados)

Primera ejecución: más lenta por descargas y preprocesado.
Siguientes ejecuciones: lectura directa de cachés.

## Explicabilidad (v1)
Reglas deterministas y cortas:
- `safe`: explica reducción de exposición y posible incremento de distancia vs baseline más rápida.
- `balanced`: explica compromiso distancia/seguridad.
- `night`: explica iluminación media y riesgo nocturno agregado.
- `fastest`: explica optimización pura por distancia.

## Limitaciones conocidas
- Iluminación nocturna es una proxy por densidad de farolas (sin fotometría).
- Dataset de farolas excluye parques/jardines y M-30, por lo que se usan fallbacks neutros en celdas sin datos.
- Muestreo de edges por 3 puntos (inicio/mitad/fin): suficiente para v1, mejorable en slices futuros.

## Criterios de aceptación del slice
- `POST /api/routes` responde para `fastest`, `safe`, `balanced`, `night`.
- Las rutas cambian de forma real según el modo (costes distintos).
- Se devuelven explicaciones y métricas de resumen por ruta.
- Frontend permite seleccionar y ejecutar los cuatro modos sin mensajes de “próximamente”.

## Verificación manual
1. Arrancar backend y frontend.
2. Calcular misma OD (por ejemplo Plaza de Castilla → Matadero Madrid) en los cuatro modos.
3. Verificar cambios de geometría/longitud entre modos.
4. Verificar en tarjeta:
   - modo
   - distancia
   - seguridad/iluminación
   - explicaciones (safe/balanced/night)
5. Activar capa de seguridad y comprobar que la ruta sigue visible por encima.
