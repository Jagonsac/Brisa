# BiciMAD station mapping

The backend's [`station_normalizer.py`](../../backend/app/utils/station_normalizer.py) converts provider payloads into the [stations contract](stations.contract.json). Only entries with an ID, name, and valid coordinates survive normalization.

| Brisa field | GBFS `data.stations[]` | EMT GeoJSON feature |
| --- | --- | --- |
| `id` | `station_id` | `properties.station_id`, `id`, or `number` |
| `name` | `name` | `properties.name` or `nombre` |
| `lat` | `lat` | `geometry.coordinates[1]` |
| `lon` | `lon` or `lng` | `geometry.coordinates[0]` |
| `address` | `address` | `properties.address` or `direccion` |
| `capacity` | `capacity` | `properties.capacity` or `dock_bikes` |

Numeric coordinates/capacity are parsed when possible. IDs become strings. Address and capacity may be null. Invalid coordinates, IDs, or names cause that station to be skipped.

`BicimadService` tries GBFS station information, then the official EMT GeoJSON, then the local snapshot when `source=auto`. `source=remote` permits the two remote sources but fails rather than using the local snapshot. Successful remote loads attempt to persist a new snapshot. Metadata reports `count`, `source`, `fallbackUsed`, and warnings; station count is not a fixed project statistic.

The frontend has its own provider/snapshot normalization fallback. These are location feeds, not a guarantee of live bike/dock availability. Current route station choice does not consult the separate status service. See [known issues](../known-issues.md#bicimad-selection-and-explanation-disagree) and the [architecture](../architecture.md).
