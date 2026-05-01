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
        _row("a", {"safety": 0.9, "bike_infra": 0.8, "low_hostility": 0.7, "green_cyclable": 0.85, "night": 0.75, "junction": 0.5, "bicimad": 0.8}),
        _row("b", {"safety": 0.6, "bike_infra": 0.5, "low_hostility": 0.6, "green_cyclable": 0.45, "night": 0.45, "junction": 0.4, "bicimad": 0.4}),
        _row("c", {"safety": 0.25, "bike_infra": 0.3, "low_hostility": 0.2, "green_cyclable": 0.15, "night": 0.2, "junction": 0.35, "bicimad": 0.1}),
    ]

    normalized = service._normalize_scores(rows)
    ranked = service._build_ranked_payload(normalized)

    assert ranked[0]["cyclabilityScore"] >= ranked[-1]["cyclabilityScore"]

    for row in ranked:
        assert 0 <= row["cyclabilityScore"] <= 100
        assert 0 <= row["safetyScore"] <= 100
        assert 0 <= row["bikeInfraScore"] <= 100
        assert 0 <= row["lowHostilityScore"] <= 100
        assert 0 <= row["greenCyclableScore"] <= 100
        assert 0 <= row["nightScore"] <= 100
        assert 0 <= row["junctionScore"] <= 100
        assert 0 <= row["bicimadScore"] <= 100


def test_green_cyclable_score_rewards_legal_green_network():
    service = CyclabilityService()
    rows = [
        _row("green", {"safety": 0.6, "bike_infra": 0.6, "low_hostility": 0.6, "green_cyclable": 0.9, "night": 0.6, "junction": 0.6, "bicimad": 0.3}),
        _row("urban", {"safety": 0.6, "bike_infra": 0.6, "low_hostility": 0.6, "green_cyclable": 0.2, "night": 0.6, "junction": 0.6, "bicimad": 0.3}),
    ]

    ranked = service._build_ranked_payload(service._normalize_scores(rows))
    index = {row["neighborhoodId"]: row for row in ranked}
    assert index["green"]["greenCyclableScore"] > index["urban"]["greenCyclableScore"]


def test_served_area_ratio_reduces_large_area_penalty():
    service = CyclabilityService()
    ratio_small = service._served_area_ratio(total_length_m=5_000, area_km2=1.0)
    ratio_large = service._served_area_ratio(total_length_m=5_000, area_km2=8.0)
    assert ratio_small > ratio_large
    assert 0.15 <= ratio_large <= 1.0


def test_bike_accident_exposure_proxy_is_stable():
    service = CyclabilityService()
    high_exposure = service._bike_exposure_proxy(bike_presence=0.8, bike_metric=0.6)
    low_exposure = service._bike_exposure_proxy(bike_presence=0.0, bike_metric=0.0)
    assert high_exposure > low_exposure
    assert low_exposure == 0.05


def test_bicimad_signal_does_not_collapse_to_zero():
    service = CyclabilityService()
    rows = [
        _row("dense", {"safety": 0.7, "bike_infra": 0.6, "low_hostility": 0.6, "green_cyclable": 0.5, "night": 0.6, "junction": 0.6, "bicimad": 0.8}),
        _row("with_signal", {"safety": 0.7, "bike_infra": 0.6, "low_hostility": 0.6, "green_cyclable": 0.5, "night": 0.6, "junction": 0.6, "bicimad": 0.02}),
        _row("none", {"safety": 0.7, "bike_infra": 0.6, "low_hostility": 0.6, "green_cyclable": 0.5, "night": 0.6, "junction": 0.6, "bicimad": 0.0}),
    ]
    rows[1]["metrics"].update({"bicimadStationsCount": 2, "bicimadCoverage": 0.08})
    rows[2]["metrics"].update({"bicimadStationsCount": 0, "bicimadCoverage": 0.0})

    ranked = service._build_ranked_payload(service._normalize_scores(rows))
    index = {row["neighborhoodId"]: row for row in ranked}
    assert index["with_signal"]["bicimadScore"] >= 6.0
    assert index["none"]["bicimadScore"] <= index["with_signal"]["bicimadScore"]


def test_data_gap_and_normalization_flags_are_separated():
    service = CyclabilityService()
    rows = [
        _row("low", {"safety": 0.1, "bike_infra": 0.03, "low_hostility": 0.2, "green_cyclable": 0.1, "night": 0.2, "junction": 0.2, "bicimad": 0.1}),
        _row("high", {"safety": 0.9, "bike_infra": 0.8, "low_hostility": 0.9, "green_cyclable": 0.7, "night": 0.8, "junction": 0.8, "bicimad": 0.8}),
    ]
    rows[0]["metrics"]["networkKm"] = 1.0
    ranked = service._build_ranked_payload(service._normalize_scores(rows))
    low_row = next(row for row in ranked if row["neighborhoodId"] == "low")

    assert low_row["dataQuality"]["status"] == "fully_observed"
    assert "bike_infra" in low_row["normalizationFlags"]
    assert "bike_infra" in low_row["performanceFlags"]
