# Mapeo de estaciones Bicimad (Slice 3)

## Fuentes externas contempladas
- Principal: `station_information` de GBFS Madrid.
- Fallback remoto oficial: GeoJSON de EMT Madrid.
- Fallback local: snapshot en `backend/app/data/bicimad_stations_snapshot.json`.

## Campos del proveedor que usamos en Brisa
### Desde GBFS `station_information`
- `station_id` → `data[].id`
- `name` → `data[].name`
- `lat` → `data[].lat`
- `lon` (o `lng` si aparece) → `data[].lon`
- `address` → `data[].address`
- `capacity` → `data[].capacity`

### Desde fallback GeoJSON EMT
- `properties.station_id`/`properties.id`/`properties.number` → `data[].id`
- `properties.name`/`properties.nombre` → `data[].name`
- `geometry.coordinates[1]` → `data[].lat`
- `geometry.coordinates[0]` → `data[].lon`
- `properties.address`/`properties.direccion` → `data[].address`
- `properties.capacity`/`properties.dock_bikes` → `data[].capacity`

## Contrato API que consume el frontend
```json
{
  "data": [
    {
      "id": "2255",
      "name": "319 - Valdesangil",
      "lat": 40.4684218,
      "lon": -3.7166729,
      "address": "Calle Valdesangil, 34",
      "capacity": 44
    }
  ],
  "meta": {
    "count": 611,
    "source": "gbfs-station-information",
    "fallbackUsed": false,
    "warnings": []
  }
}
```

## Campos fuera de alcance en Slice 3
- Disponibilidad en tiempo real (`station_status`).
- Predicción de estaciones recomendadas.
- Unificación multimodal (bici + caminar + metro).

## Preparación para slices futuros
`meta` permite trazabilidad de fuentes y degradación para introducir `station_status`, cache y combinación de datasets sin romper el contrato de UI.
