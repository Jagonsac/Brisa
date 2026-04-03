from fastapi.testclient import TestClient

from app.main import app
from app.routers import cyclability as cyclability_router


FAKE_NEIGHBORHOOD = {
    "neighborhoodId": "001",
    "name": "Sol",
    "district": "Centro",
    "cyclabilityScore": 78.5,
    "rank": 1,
    "percentile": 100,
    "safetyScore": 75,
    "bikeInfraScore": 70,
    "lowHostilityScore": 72,
    "nightScore": 65,
    "junctionScore": 68,
    "bicimadScore": 88,
    "strengths": ["Acceso a Bicimad"],
    "weaknesses": ["Comportamiento nocturno"],
    "summary": "Sol combina acceso a Bicimad.",
    "metrics": {"networkKm": 2.1},
    "dataQuality": {"status": "fully_observed", "fallbacks": []},
    "geometry": {"type": "Polygon", "coordinates": []},
}


def test_neighborhoods_endpoint(monkeypatch):
    monkeypatch.setattr(cyclability_router.service, "list_neighborhoods", lambda: {"data": [FAKE_NEIGHBORHOOD], "meta": {"city": "Madrid"}})
    client = TestClient(app)

    response = client.get("/api/cyclability/neighborhoods")
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"][0]["name"] == "Sol"


def test_detail_and_compare_endpoints(monkeypatch):
    monkeypatch.setattr(cyclability_router.service, "get_neighborhood_detail", lambda _: {"data": FAKE_NEIGHBORHOOD, "meta": {}})
    monkeypatch.setattr(
        cyclability_router.service,
        "compare",
        lambda _left, _right: {"data": {"left": FAKE_NEIGHBORHOOD, "right": FAKE_NEIGHBORHOOD, "breakdown": []}, "meta": {}},
    )
    client = TestClient(app)

    detail = client.get("/api/cyclability/neighborhoods/001")
    compare = client.get("/api/cyclability/neighborhoods/compare?left=001&right=001")

    assert detail.status_code == 200
    assert compare.status_code == 200
    assert compare.json()["data"]["left"]["neighborhoodId"] == "001"
