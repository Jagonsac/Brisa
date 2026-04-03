from app.services.cyclability_service import CyclabilityService


def _row(neighborhood_id: str, raw: dict[str, float]) -> dict:
    return {
        "neighborhoodId": neighborhood_id,
        "name": neighborhood_id,
        "district": "Centro",
        "geometry": {"type": "Polygon", "coordinates": []},
        "metrics": {"networkKm": 1.2},
        "raw": raw,
    }


def test_scores_are_bounded_and_sorted():
    service = CyclabilityService()
    rows = [
        _row("a", {"safety": 0.9, "bike_infra": 0.8, "low_hostility": 0.7, "night": 0.75, "junction": 0.5, "bicimad": 0.8}),
        _row("b", {"safety": 0.6, "bike_infra": 0.5, "low_hostility": 0.6, "night": 0.45, "junction": 0.4, "bicimad": 0.4}),
        _row("c", {"safety": 0.25, "bike_infra": 0.3, "low_hostility": 0.2, "night": 0.2, "junction": 0.35, "bicimad": 0.1}),
    ]

    normalized = service._normalize_scores(rows)
    ranked = service._build_ranked_payload(normalized)

    assert ranked[0]["cyclabilityScore"] >= ranked[-1]["cyclabilityScore"]

    for row in ranked:
        assert 0 <= row["cyclabilityScore"] <= 100
        assert 0 <= row["safetyScore"] <= 100
        assert 0 <= row["bikeInfraScore"] <= 100
        assert 0 <= row["lowHostilityScore"] <= 100
        assert 0 <= row["nightScore"] <= 100
        assert 0 <= row["junctionScore"] <= 100
        assert 0 <= row["bicimadScore"] <= 100
