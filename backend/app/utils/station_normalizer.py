from app.schemas.station import Station


def _has_valid_coordinates(lat: float, lon: float) -> bool:
    return -90 <= lat <= 90 and -180 <= lon <= 180


def _to_station(id: str | None, name: str | None, lat: float, lon: float, address: str | None, capacity: float | None) -> Station | None:
    if not id or not name:
        return None

    if not _has_valid_coordinates(lat, lon):
        return None

    return Station(
        id=str(id),
        name=str(name),
        lat=lat,
        lon=lon,
        address=str(address) if address else None,
        capacity=capacity if isinstance(capacity, (int, float)) else None,
    )


def normalize_gbfs_stations(payload: dict) -> list[Station]:
    stations = payload.get("data", {}).get("stations", [])
    if not isinstance(stations, list):
        return []

    normalized = []
    for station in stations:
        lat = _to_float(station.get("lat"))
        lon = _to_float(station.get("lon") or station.get("lng"))
        if lat is None or lon is None:
            continue

        normalized_station = _to_station(
            id=station.get("station_id"),
            name=station.get("name"),
            lat=lat,
            lon=lon,
            address=station.get("address"),
            capacity=_to_float(station.get("capacity")),
        )
        if normalized_station:
            normalized.append(normalized_station)

    return normalized


def normalize_geojson_stations(payload: dict) -> list[Station]:
    features = payload.get("features", [])
    if not isinstance(features, list):
        return []

    normalized = []
    for feature in features:
        properties = feature.get("properties", {})
        coordinates = feature.get("geometry", {}).get("coordinates", [])
        lon = _to_float(coordinates[0]) if len(coordinates) > 0 else None
        lat = _to_float(coordinates[1]) if len(coordinates) > 1 else None
        if lat is None or lon is None:
            continue

        normalized_station = _to_station(
            id=properties.get("station_id") or properties.get("id") or properties.get("number"),
            name=properties.get("name") or properties.get("nombre"),
            lat=lat,
            lon=lon,
            address=properties.get("address") or properties.get("direccion"),
            capacity=_to_float(properties.get("capacity") or properties.get("dock_bikes")),
        )
        if normalized_station:
            normalized.append(normalized_station)

    return normalized


def normalize_snapshot_stations(payload: list[dict]) -> list[Station]:
    if not isinstance(payload, list):
        return []

    normalized = []
    for station in payload:
        lat = _to_float(station.get("lat"))
        lon = _to_float(station.get("lon"))
        if lat is None or lon is None:
            continue

        normalized_station = _to_station(
            id=station.get("station_id") or station.get("id"),
            name=station.get("name"),
            lat=lat,
            lon=lon,
            address=station.get("address"),
            capacity=_to_float(station.get("capacity")),
        )
        if normalized_station:
            normalized.append(normalized_station)

    return normalized


def _to_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
