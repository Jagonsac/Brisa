def build_route_geojson_feature(coordinates: list[list[float]], distance_meters: float, mode: str, profile: str) -> dict:
    return {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": coordinates,
        },
        "properties": {
            "distanceMeters": round(distance_meters, 2),
            "mode": mode,
            "profile": profile,
        },
    }
