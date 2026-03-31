# Slice 4 — Routing real más corto (OSMnx + FastAPI)

## Objetivo del slice
Entregar la primera ruta real de Brisa entre origen y destino usando red ciclista de OpenStreetMap, calculada en backend y dibujada en el mapa frontend.

## Decisión de datos
En este slice usamos exclusivamente OSM + OSMnx para:
- geocodificación con Nominatim
- descarga/caché de red bikeable de Madrid
- shortest path por distancia (`length`)

No se incorporan todavía datasets municipales de accidentes, tráfico o barrios porque pertenecen a slices posteriores (5 y 6).

## Arquitectura del flujo
1. El usuario envía origen/destino en React.
2. Frontend llama a `POST /api/routes`.
3. Backend geocodifica ambos puntos contra Nominatim.
4. Backend carga el grafo bike de Madrid desde cache (`graphml`) o lo descarga una vez.
5. Backend hace snapping a nodos y calcula ruta más corta por `length`.
6. Backend devuelve GeoJSON + resumen + metadatos.
7. Frontend dibuja ruta, origen/destino y resumen mínimo.

## Contrato
- Request: `docs/contracts/route-request.contract.json`
- Response: `docs/contracts/route-response.contract.json`

## Estrategia de geocoding
- Query enriquecida con `, Madrid, Spain` cuando el usuario no incluye Madrid.
- `format=jsonv2`, `limit=1`, `countrycodes=es`, `addressdetails=1`.
- `User-Agent` configurable por entorno.

## Estrategia de caché del grafo
- Ruta de persistencia: `backend/data/graphs/madrid_bike.graphml`.
- Lazy load: el grafo se carga bajo demanda en la primera petición.
- Si no existe el archivo, se descarga con OSMnx y se guarda.
- Si ya existe, se carga desde cache en disco y luego en memoria.

## Criterios de aceptación
- Backend mantiene `GET /health`.
- `POST /api/routes` devuelve ruta real para `mode=fastest`.
- Frontend dibuja la ruta y muestra resumen de distancia.
- Modos no implementados (`safe`, `balanced`, `night`) muestran estado honesto de “próximamente”.

## Verificación manual
1. Arrancar backend y frontend.
2. En UI introducir `Atocha` y `Plaza de Castilla` con modo `Rápida`.
3. Confirmar que aparece línea de ruta y resumen de km.
4. Cambiar a modo `Segura` y verificar mensaje de “próximamente”.

## Limitaciones actuales
- La primera petición puede tardar por descarga inicial del grafo.
- Geocodificación depende de Nominatim y puede devolver resultados ambiguos.
- Solo existe estrategia `fastest` por distancia (sin score de seguridad todavía).
