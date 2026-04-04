from app.services.station_status_service import StationStatusService
from app.utils.route_payload_parser import parse_route_payload


def test_parse_route_payload_with_bicimad_flags():
    parsed = parse_route_payload(
        {
            "origin": {"query": "A"},
            "destination": {"query": "B"},
            "mode": "safe",
            "useBicimad": True,
        }
    )
    assert parsed.use_bicimad is True

    parsed_transport = parse_route_payload(
        {
            "origin": {"query": "A"},
            "destination": {"query": "B"},
            "mode": "safe",
            "transportMode": "bicimad",
        }
    )
    assert parsed_transport.use_bicimad is True


def test_station_status_normalizer_handles_expected_fields():
    payload = {
        "data": {
            "stations": [
                {
                    "station_id": "10",
                    "num_bikes_available": 5,
                    "num_docks_available": 9,
                    "is_renting": 1,
                    "is_returning": 1,
                    "is_installed": 1,
                }
            ]
        }
    }

    normalized = StationStatusService._normalize(payload)
    assert normalized["10"]["bikesAvailable"] == 5
    assert normalized["10"]["docksAvailable"] == 9
    assert normalized["10"]["isInstalled"] is True
