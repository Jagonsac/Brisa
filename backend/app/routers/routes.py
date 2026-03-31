from fastapi import APIRouter, HTTPException, status

from app.schemas.route_request import RouteRequest
from app.schemas.route_response import RouteResponse
from app.services.route_service import RouteService, RouteServiceError

router = APIRouter(prefix="/api/routes", tags=["routes"])
service = RouteService()


@router.post("", response_model=RouteResponse)
async def create_route(payload: RouteRequest) -> RouteResponse:
    if payload.mode != "fastest":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "mode_not_available",
                "message": "Solo el modo rápida está disponible por ahora.",
            },
        )

    try:
        return await service.build_fastest_route(
            origin_query=payload.originQuery.strip(),
            destination_query=payload.destinationQuery.strip(),
            mode=payload.mode,
        )
    except RouteServiceError as error:
        status_by_code = {
            "invalid_query": status.HTTP_400_BAD_REQUEST,
            "location_not_found": status.HTTP_404_NOT_FOUND,
            "route_not_found": status.HTTP_404_NOT_FOUND,
            "graph_warming_up": status.HTTP_503_SERVICE_UNAVAILABLE,
            "snap_failed": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "invalid_provider_payload": status.HTTP_502_BAD_GATEWAY,
        }
        raise HTTPException(
            status_code=status_by_code.get(error.code, status.HTTP_500_INTERNAL_SERVER_ERROR),
            detail={"code": error.code, "message": error.message},
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "internal_error",
                "message": "No fue posible calcular la ruta en este momento.",
            },
        ) from error
