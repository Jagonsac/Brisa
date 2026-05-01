import pytest

from app.services.geocoding_service import GeocodingService


@pytest.mark.asyncio
async def test_suggest_uses_structured_query_when_street_number_present():
    service = GeocodingService(client=None)

    async def fake_structured(**kwargs):
        assert kwargs["street"] == "45 calle de Alcalá"
        return [
            {
                "display_name": "Calle de Alcalá, 45, Salamanca, Madrid, España",
                "lat": "40.123",
                "lon": "-3.456",
                "address": {"road": "Calle de Alcalá", "house_number": "45"},
            }
        ]

    async def fake_freeform(*args, **kwargs):
        raise AssertionError("Free-form fallback should not be used when structured search returns data")

    service._search_nominatim_structured = fake_structured
    service._search_nominatim = fake_freeform

    suggestions = await service.suggest("calle de Alcalá 45")
    assert len(suggestions) == 1
    assert suggestions[0]["displayText"] == "Calle de Alcalá, 45"


@pytest.mark.asyncio
async def test_suggest_falls_back_to_freeform_when_structured_has_no_results():
    service = GeocodingService(client=None)

    async def fake_structured(**kwargs):
        return []

    async def fake_freeform(query, **kwargs):
        assert query == "calle de Alcalá 45"
        return [
            {
                "display_name": "Calle de Alcalá, Salamanca, Madrid, Comunidad de Madrid, España",
                "lat": "40.123",
                "lon": "-3.456",
                "address": {"road": "Calle de Alcalá", "house_number": "45"},
            }
        ]

    service._search_nominatim_structured = fake_structured
    service._search_nominatim = fake_freeform

    suggestions = await service.suggest("calle de Alcalá 45")
    assert len(suggestions) == 1
    assert suggestions[0]["displayText"] == "Calle de Alcalá, 45"


def test_structured_street_query_parser_extracts_house_number():
    assert GeocodingService._to_structured_street_query("calle de Alcalá 45") == "45 calle de Alcalá"
    assert GeocodingService._to_structured_street_query("45 calle de Alcalá") is None
