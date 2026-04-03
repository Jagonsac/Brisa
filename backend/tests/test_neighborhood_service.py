from shapely.geometry import Polygon

from app.services.neighborhood_service import NeighborhoodArea, NeighborhoodService


def _neighborhood(neighborhood_id: str, polygon: Polygon) -> NeighborhoodArea:
    return NeighborhoodArea(
        neighborhood_id=neighborhood_id,
        name=neighborhood_id,
        district="D",
        geometry={"type": "Polygon", "coordinates": []},
        projected_geometry=polygon,
        bounds_projected=polygon.bounds,
    )


def test_resolve_neighborhood_projected_point_hits_polygon_boundary():
    service = NeighborhoodService()
    neighborhoods = [
        _neighborhood("a", Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])),
        _neighborhood("b", Polygon([(20, 0), (30, 0), (30, 10), (20, 10)])),
    ]

    resolved = service.resolve_neighborhood_projected_point(10, 5, neighborhoods)

    assert resolved is not None
    assert resolved.neighborhood_id == "a"


def test_nearest_neighborhood_projected_uses_geometry_distance():
    service = NeighborhoodService()
    neighborhoods = [
        _neighborhood("a", Polygon([(0, 0), (8, 0), (8, 8), (0, 8)])),
        _neighborhood("b", Polygon([(12, 0), (20, 0), (20, 8), (12, 8)])),
    ]

    resolved = service.nearest_neighborhood_projected(9.1, 4, neighborhoods)

    assert resolved is not None
    assert resolved.neighborhood_id == "b"
