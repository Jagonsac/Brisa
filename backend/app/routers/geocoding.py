from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.geocoding import GeocodingSuggestResponse
from app.services.geocoding_service import GeocodingError, GeocodingService

router = APIRouter(prefix="/api/geocoding", tags=["geocoding"])
service = GeocodingService()


@router.get("/suggest", response_model=GeocodingSuggestResponse)
async def suggest_locations(q: str = Query(min_length=1, max_length=120)) -> GeocodingSuggestResponse:
    try:
        suggestions = await service.suggest(q)
    except GeocodingError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": error.code, "message": error.message},
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "suggest_unavailable",
                "message": "No se pudieron obtener sugerencias en este momento.",
            },
        ) from error

    return GeocodingSuggestResponse(data=suggestions, meta={"count": len(suggestions)})
