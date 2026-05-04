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
