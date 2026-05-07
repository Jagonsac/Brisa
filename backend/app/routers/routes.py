import asyncio

from fastapi import APIRouter, Body, HTTPException, status

from app.schemas.route_response import RouteResponse
from app.services.route_service import RouteService, RouteServiceError
from app.utils.route_payload_parser import RoutePayloadError, parse_route_payload

router = APIRouter(prefix="/api/routes", tags=["routes"])
service = RouteService()


async def warmup_route_graph() -> None:
    await asyncio.to_thread(service.warmup_routing_engine)


@router.post("", response_model=RouteResponse)
async def create_route(payload: dict = Body(...)) -> RouteResponse:
    try:
        normalized_payload = parse_route_payload(payload)
    except RoutePayloadError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "invalid_route_request",
                "message": error.message,
            },
        ) from error

    try:
        return await service.build_route(
            origin_query=normalized_payload.origin.query,
            destination_query=normalized_payload.destination.query,
            mode=normalized_payload.mode,
            origin_lat=normalized_payload.origin.lat,
            origin_lon=normalized_payload.origin.lon,
            destination_lat=normalized_payload.destination.lat,
            destination_lon=normalized_payload.destination.lon,
            use_bicimad=normalized_payload.use_bicimad,
        )
    except RouteServiceError as error:
        status_by_code = {
            "invalid_query": status.HTTP_400_BAD_REQUEST,
            "location_not_found": status.HTTP_404_NOT_FOUND,
            "route_not_found": status.HTTP_404_NOT_FOUND,
            "graph_warming_up": status.HTTP_503_SERVICE_UNAVAILABLE,
            "snap_failed": status.HTTP_404_NOT_FOUND,
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
    finally:
        service.release_runtime_caches()
