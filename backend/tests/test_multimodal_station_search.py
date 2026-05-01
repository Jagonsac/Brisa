from types import SimpleNamespace

from app.services.geocoding_service import GeocodedPoint
from app.services.route_service import RouteService


def _station(station_id: str, lat: float, lon: float):
    return SimpleNamespace(id=station_id, name=station_id, lat=lat, lon=lon)


def test_station_candidates_prioritize_near_rings():
    service = RouteService()
    point = GeocodedPoint(query="o", display_name="o", lat=40.4168, lon=-3.7038)
    stations = [
        _station("a", 40.4168, -3.7038),
        _station("b", 40.4178, -3.7038),
        _station("c", 40.4198, -3.7038),
        _station("d", 40.4230, -3.7038),
    ]

    candidates = service._pick_station_candidates(stations, point)

    ring_indexes = [candidate["ring_index"] for candidate in candidates]
    assert ring_indexes == sorted(ring_indexes)
    assert candidates[0]["station"].id == "a"


def test_branch_and_bound_prunes_pairs():
    service = RouteService()
    origin = GeocodedPoint(query="o", display_name="o", lat=40.4168, lon=-3.7038)
    destination = GeocodedPoint(query="d", display_name="d", lat=40.4268, lon=-3.6938)

    dep = [{"station": _station(f"dep{i}", 40.4168 + i * 0.0005, -3.7038), "distance": 100 + i * 40, "ring_index": 0, "score": 0} for i in range(6)]
    arr = [{"station": _station(f"arr{i}", 40.4268 + i * 0.0005, -3.6938), "distance": 100 + i * 40, "ring_index": 0, "score": 0} for i in range(6)]

    def fake_walk(*args, **kwargs):
        return {"duration_seconds": 90, "distance_meters": 120, "coordinates": [[0, 0], [1, 1]]}

    def fake_bike(*args, **kwargs):
        dep_lat = args[4]
        arr_lat = args[6]
        spread = abs(arr_lat - dep_lat) * 100000
        return {
            "duration_seconds": 50 + spread,
            "distance_meters": 800 + spread,
            "coordinates": [[0, 0], [1, 1]],
            "avg_safety_risk": 0.2,
            "avg_lighting_deficit": 0.2,
            "avg_night_risk": 0.2,
            "avg_traffic": 0.2,
            "avg_junction": 0.2,
            "avg_bike_infra": 0.8,
        }

    service._compute_walk_leg = fake_walk
    service._compute_bike_leg = fake_bike

    _, bounded_metrics = service._evaluate_station_pairs(
        dep_candidates=dep,
        arr_candidates=arr,
        walk_graph=None,
        bike_graph=None,
        edge_metrics={},
        bike_weight_name="brisa_weight_safe",
        origin=origin,
        destination=destination,
        mode="safe",
        enable_bound=True,
    )
    _, baseline_metrics = service._evaluate_station_pairs(
        dep_candidates=dep,
        arr_candidates=arr,
        walk_graph=None,
        bike_graph=None,
        edge_metrics={},
        bike_weight_name="brisa_weight_safe",
        origin=origin,
        destination=destination,
        mode="safe",
        enable_bound=False,
    )

    assert bounded_metrics["pairs_evaluated_full"] < baseline_metrics["pairs_evaluated_full"]
    assert bounded_metrics["pairs_pruned_bound"] > 0


def test_branch_and_bound_keeps_solution_quality():
    service = RouteService()
    origin = GeocodedPoint(query="o", display_name="o", lat=40.4168, lon=-3.7038)
    destination = GeocodedPoint(query="d", display_name="d", lat=40.4268, lon=-3.6938)
    dep = [{"station": _station(f"dep{i}", 40.4168 + i * 0.0004, -3.7038), "distance": 100 + i * 20, "ring_index": 0, "score": 0} for i in range(5)]
    arr = [{"station": _station(f"arr{i}", 40.4268 + i * 0.0004, -3.6938), "distance": 100 + i * 20, "ring_index": 0, "score": 0} for i in range(5)]

    service._compute_walk_leg = lambda *args, **kwargs: {"duration_seconds": 80, "distance_meters": 100, "coordinates": [[0, 0], [1, 1]]}
    service._compute_bike_leg = lambda *args, **kwargs: {
        "duration_seconds": 120,
        "distance_meters": 900,
        "coordinates": [[0, 0], [1, 1]],
        "avg_safety_risk": 0.2,
        "avg_lighting_deficit": 0.2,
        "avg_night_risk": 0.2,
        "avg_traffic": 0.2,
        "avg_junction": 0.2,
        "avg_bike_infra": 0.8,
    }

    bounded_plan, _ = service._evaluate_station_pairs(dep_candidates=dep, arr_candidates=arr, walk_graph=None, bike_graph=None, edge_metrics={}, bike_weight_name="w", origin=origin, destination=destination, mode="balanced", enable_bound=True)
    baseline_plan, _ = service._evaluate_station_pairs(dep_candidates=dep, arr_candidates=arr, walk_graph=None, bike_graph=None, edge_metrics={}, bike_weight_name="w", origin=origin, destination=destination, mode="balanced", enable_bound=False)

    assert bounded_plan is not None and baseline_plan is not None
    assert abs(bounded_plan["score"] - baseline_plan["score"]) < 1e-6
