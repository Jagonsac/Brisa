# Slice 2 — Estaciones Bicimad en mapa

## Objetivo del slice
Integrar estaciones Bicimad reales en Brisa de forma modular, manteniendo mapa y UI estables, con fallback robusto para demo aunque fallen fuentes remotas.

## Fuentes de datos usadas
- Principal GBFS: `https://madrid.publicbikesystem.net/customer/gbfs/v2/es/station_information`
- Feed raíz de referencia: `https://madrid.publicbikesystem.net/customer/gbfs/v2/gbfs.json`
- Fallback oficial: `https://datos.emtmadrid.es/dataset/5fcc0945-2cbd-46c3-801a-6a83f4167c11/resource/105ce5df-793f-4e0a-a88e-5d3b3f024a5d/download/bikestationbicimad_geojson.geojson`
- Preparado para futuro: `https://madrid.publicbikesystem.net/customer/gbfs/v2/es/station_status` (no consumido todavía)

## Contrato interno adoptado
La UI consume estaciones normalizadas con este contrato estable:
- `id` (string, obligatorio)
- `name` (string, obligatorio)
- `lat` (number, obligatorio)
- `lon` (number, obligatorio)
- `address` (string|null)
- `capacity` (number|null)

Referencia formal: `docs/contracts/stations.contract.json`.

## Decisiones de arquitectura
1. **Servicio aislado por feature** (`src/features/bicimad/services`): selección de fuente y fallback fuera de componentes visuales.
2. **Normalización dedicada** (`src/features/bicimad/utils`): el mapa nunca consume JSON crudo de proveedor.
3. **Hook encapsulado** (`useBicimadStations`): gestiona `loading`, `error`, `source`, `usedFallback`, `stations`.
4. **Capa visual desacoplada** (`BicimadStationsLayer`): solo render de estaciones normalizadas.
5. **Feature flags**: `enableBicimad` y `enableBicimadStationsLayer` para activar/desactivar sin tocar código de mapa.

## Estrategia de fallback y robustez
Secuencia de carga:
1. Intento `station_information` GBFS.
2. Si falla o no trae estaciones válidas, intento fallback GeoJSON EMT.
3. Si también falla, uso snapshot local (`src/mocks/bicimadStationsSnapshot.js`).
4. Si todo falla, se muestra error limpio en UI sin romper mapa.

Adicionalmente:
- Timeout por petición (8s).
- Manejo de `AbortController`.
- Filtrado de estaciones inválidas sin coordenadas válidas.

## Cambios funcionales visibles
- Mapa ahora muestra estaciones Bicimad con `CircleMarker` y popup mínimo (nombre, dirección, capacidad, etiqueta Bicimad).
- Nuevo bloque lateral de estado Bicimad con estados:
  - loading
  - error
  - fallback activo
  - sin datos
- Panel de estado del producto marca Slice 2 de Bicimad como completado.

## Criterios de aceptación del slice
- App ejecuta con `npm install` y `npm run dev`.
- Slice 1 se mantiene funcional.
- Estaciones Bicimad visibles en mapa cuando la feature está activa.
- Sin lógica de fetch en componentes visuales.
- Contrato de estaciones documentado.
- Fallback operativo para demo estable.

## Verificación manual
1. Ejecutar `npm install`.
2. Ejecutar `npm run dev`.
3. Abrir la app y verificar que el mapa carga como en Slice 1.
4. Confirmar que aparecen estaciones Bicimad (marcadores azules).
5. Pulsar una estación y verificar popup con campos mínimos.
6. Revisar bloque "Bicimad" en sidebar para estado de carga/fuente/fallback.
7. (Opcional) forzar fallo de red y comprobar degradación elegante.
