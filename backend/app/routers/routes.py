from fastapi import APIRouter, HTTPException

from app.schemas.route_request import RouteRequest
from app.schemas.route_response import RouteResponse
from app.services.route_service import RouteService

router = APIRouter(prefix="/api/routes", tags=["routes"])
service = RouteService()


@router.post("", response_model=RouteResponse)
async def create_route(payload: RouteRequest) -> RouteResponse:
    if payload.mode != "fastest":
        raise HTTPException(status_code=422, detail="Solo el modo 'fastest' está disponible en Slice 4.")

    try:
        return await service.build_fastest_route(
            origin_query=payload.originQuery.strip(),
            destination_query=payload.destinationQuery.strip(),
            mode=payload.mode,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail="No fue posible calcular la ruta en este momento.") from error
