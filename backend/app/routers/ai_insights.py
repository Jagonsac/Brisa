from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException, Request

from app.services.ai_route_insights_service import AIRouteInsightsError, AIRouteInsightsService

router = APIRouter(prefix="/api/ai", tags=["ai"])
service = AIRouteInsightsService()


@router.post("/route-insights")
async def route_insights(request: Request, payload: dict = Body(...)) -> dict:
    routes = payload.get("routes")
    if not isinstance(routes, list):
        raise HTTPException(status_code=400, detail={"code": "invalid_ai_request", "message": "El campo routes debe ser una lista."})

    client_key = request.client.host if request.client else "unknown"
    try:
        result = await service.analyze_routes(routes=routes, client_key=client_key)
        return {"data": result, "meta": {"model": service.model, "cached": False}}
    except AIRouteInsightsError as error:
        raise HTTPException(status_code=error.status_code, detail={"code": error.code, "message": error.message}) from error
