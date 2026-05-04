from types import SimpleNamespace

from app.services.geocoding_service import GeocodedPoint
from app.services.route_service import RouteService


class _GraphStub:
    def __init__(self):
        self.graph = {"network_type": "bike"}


def test_build_bike_route_uses_bike_leg_hazards(monkeypatch):
    service = RouteService()

    monkeypatch.setattr(service.graph_service, "get_graph", lambda network_type="bike": (_GraphStub(), "cache"))
    monkeypatch.setattr(service.edge_weight_service, "get_edge_weights", lambda: {"version": "v1", "edges": {}})
    monkeypatch.setattr(service, "_ensure_graph_weights", lambda *args, **kwargs: None)
    monkeypatch.setattr(service, "_resolve_nearest_node", lambda *args, **kwargs: 1)
    monkeypatch.setattr(
        service,
        "_compute_path",
        lambda *args, **kwargs: {
            "coordinates": [[-3.7, 40.4], [-3.69, 40.41]],
            "distance_meters": 1200.0,
            "avg_safety_risk": 0.2,
            "avg_lighting_deficit": 0.3,
            "avg_night_risk": 0.25,
            "avg_traffic": 0.4,
            "avg_junction": 0.5,
            "avg_bike_infra": 0.6,
            "hazard_points": [{"type": "dangerous_junction", "lat": 40.405, "lon": -3.695}],
        },
    )
    monkeypatch.setattr(service, "_estimate_baseline_fastest", lambda *args, **kwargs: 1100.0)

    origin = GeocodedPoint(query="a", display_name="A", lat=40.4, lon=-3.7)
    destination = GeocodedPoint(query="b", display_name="B", lat=40.41, lon=-3.69)

    response = service._build_bike_route(origin=origin, destination=destination, mode="safe")

    assert response.data.hazardPoints
    assert response.data.hazardPoints[0].type == "dangerous_junction"
