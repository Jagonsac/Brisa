from app.services.bike_legality_service import evaluate_bike_legality


def test_excludes_bicycle_no_and_motorroad():
    assert evaluate_bike_legality({"highway": "primary", "bicycle": "no"}).allowed is False
    assert evaluate_bike_legality({"highway": "primary", "motorroad": "yes"}).allowed is False


def test_excludes_motorway_and_motorway_link():
    assert evaluate_bike_legality({"highway": "motorway"}).allowed is False
    assert evaluate_bike_legality({"highway": "motorway_link"}).allowed is False


def test_trunk_without_cycle_infra_is_blocked():
    blocked = evaluate_bike_legality({"highway": "trunk", "bicycle": "yes"})
    allowed = evaluate_bike_legality({"highway": "trunk", "cycleway": "track", "bicycle": "designated"})
    assert blocked.allowed is False
    assert allowed.allowed is True
