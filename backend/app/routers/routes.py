from fastapi import APIRouter, Body, HTTPException, status
from pydantic import ValidationError

from app.schemas.route_request import RouteRequest
from app.schemas.route_response import RouteResponse
from app.services.route_service import RouteService, RouteServiceError

router = APIRouter(prefix="/api/routes", tags=["routes"])
service = RouteService()


@router.post("", response_model=RouteResponse)
async def create_route(raw_payload: dict = Body(...)) -> RouteResponse:
    try:
        payload = RouteRequest.model_validate(raw_payload)
    except ValidationError as error:
        details = error.errors()
        missing_mode = any(err.get("loc") == ("mode",) for err in details)
        missing_origin = any(err.get("loc") == ("origin",) for err in details)
        missing_destination = any(err.get("loc") == ("destination",) for err in details)

        if missing_mode or missing_origin or missing_destination:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "invalid_route_request",
                    "message": "Faltan datos para calcular la ruta.",
                },
            ) from error

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "invalid_route_payload",
                "message": "El formato del payload de ruta no es válido.",
                "errors": details,
            },
        ) from error

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
            origin_query=payload.origin.query.strip(),
            destination_query=payload.destination.query.strip(),
            mode=payload.mode,
            origin_lat=payload.origin.lat,
            origin_lon=payload.origin.lon,
            destination_lat=payload.destination.lat,
            destination_lon=payload.destination.lon,
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
