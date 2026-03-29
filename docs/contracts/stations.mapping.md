# Mapeo de estaciones Bicimad (Slice 2)

## Fuentes externas contempladas
- Principal: `station_information` de GBFS Madrid.
- Fallback remoto oficial: GeoJSON de EMT Madrid.
- Fallback local: snapshot en `src/mocks/bicimadStationsSnapshot.js`.

## Campos del proveedor que usamos en Brisa
### Desde GBFS `station_information`
- `station_id` → `id`
- `name` → `name`
- `lat` → `lat`
- `lon` (o `lng` si aparece) → `lon`
- `address` → `address`
- `capacity` → `capacity`

### Desde fallback GeoJSON EMT
- `properties.station_id`/`properties.id`/`properties.number` → `id`
- `properties.name`/`properties.nombre` → `name`
- `geometry.coordinates[1]` → `lat`
- `geometry.coordinates[0]` → `lon`
- `properties.address`/`properties.direccion` → `address`
- `properties.capacity`/`properties.dock_bikes` → `capacity`

## Campos internos que consume la UI
Contrato reducido y estable:

```json
{
  "id": "2255",
  "name": "319 - Valdesangil",
  "lat": 40.4684218,
  "lon": -3.7166729,
  "address": "Calle Valdesangil, 34",
  "capacity": 44
}
```

## Campos explícitamente fuera de alcance en Slice 2
- Disponibilidad en tiempo real (`station_status`).
- Conteo de bicis/libres en vivo.
- Predicciones o recomendación de estación óptima.
- Cualquier lógica de combinación multimodal andando + bici.

## Preparación para slices futuros
El servicio ya expone `source` y `usedFallback` para soportar trazabilidad y facilitar la futura combinación de `station_information` + `station_status` sin romper el contrato visual actual.
