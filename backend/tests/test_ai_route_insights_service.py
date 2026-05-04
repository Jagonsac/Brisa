from app.services.ai_route_insights_service import AIRouteInsightsError, AIRouteInsightsService


def test_extract_ai_json_from_output_json_string_payload():
    service = AIRouteInsightsService()
    payload = {
        "output": [
            {
                "content": [
                    {
                        "type": "output_json",
                        "json": '{"overview":"ok","routes":[{"mode":"night","best":"","worst":"","riskLevel":"medium","tips":[]}],"globalTips":[]}',
                    }
                ]
            }
        ]
    }

    data = service._extract_ai_json(payload)

    assert data["overview"] == "ok"
    assert data["routes"][0]["mode"] == "night"


def test_extract_ai_json_from_wrapped_text_payload():
    service = AIRouteInsightsService()
    payload = {
        "output_text": "Aquí tienes el análisis:\n```json\n{\"overview\":\"ok\",\"routes\":[{\"mode\":\"fastest\",\"best\":\"\",\"worst\":\"\",\"riskLevel\":\"low\",\"tips\":[]}],\"globalTips\":[]}\n```",
    }

    data = service._extract_ai_json(payload)

    assert data["routes"][0]["mode"] == "fastest"


def test_extract_ai_json_raises_on_invalid_payload():
    service = AIRouteInsightsService()

    try:
        service._extract_ai_json({"output_text": "sin json"})
        assert False, "Expected AIRouteInsightsError"
    except AIRouteInsightsError as error:
        assert error.code == "invalid_ai_response"


def test_extract_ai_json_uses_last_valid_json_fragment_when_mixed_text_present():
    service = AIRouteInsightsService()
    payload = {
        "output": [
            {
                "content": [
                    {"type": "text", "text": "Resumen interno no JSON"},
                    {
                        "type": "output_text",
                        "text": '{"overview":"ok","routes":[{"mode":"night","best":"","worst":"","riskLevel":"medium","tips":[]}],"globalTips":[]}',
                    },
                ]
            }
        ]
    }

    data = service._extract_ai_json(payload)

    assert data["routes"][0]["mode"] == "night"


def test_extract_ai_json_prefers_output_parsed_over_other_fields():
    service = AIRouteInsightsService()
    payload = {
        "output_parsed": {
            "overview": "parsed",
            "routes": [{"mode": "night", "best": "", "worst": "", "riskLevel": "low", "tips": []}],
            "globalTips": [],
        },
        "output_text": "{\"overview\":\"text\",\"routes\":[],\"globalTips\":[]}",
    }

    data = service._extract_ai_json(payload)

    assert data["overview"] == "parsed"
