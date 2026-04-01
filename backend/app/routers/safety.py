from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.safety_grid_response import SafetyGridResponse
from app.schemas.safety_summary_response import SafetySummaryResponse
from app.services.safety_service import SafetyService

router = APIRouter(prefix="/api/safety", tags=["safety"])
service = SafetyService()


@router.get("/grid", response_model=SafetyGridResponse)
def get_safety_grid(bbox: str | None = Query(default=None, description="minLon,minLat,maxLon,maxLat")) -> SafetyGridResponse:
    try:
        parsed_bbox = None
        if bbox:
            values = [float(value.strip()) for value in bbox.split(",")]
            if len(values) != 4:
                raise ValueError("BBox inválido")
            parsed_bbox = (values[0], values[1], values[2], values[3])

        collection, metadata = service.get_grid(parsed_bbox)
        return SafetyGridResponse.model_validate(
            {
                "data": collection,
                "meta": {
                    "version": metadata.get("version", "v1"),
                    "cellSizeMeters": metadata.get("cellSizeMeters", 250),
                    "sources": metadata.get("sources", {}),
                    "trafficFallbackUsed": metadata.get("trafficFallbackUsed", True),
                },
            }
        )
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "safety_grid_unavailable", "message": f"No se pudo construir la capa de seguridad: {error}"},
        ) from error


@router.get("/summary", response_model=SafetySummaryResponse)
def get_safety_summary() -> SafetySummaryResponse:
    try:
        summary = service.get_summary()
        return SafetySummaryResponse.model_validate({"data": summary, "meta": {"ready": True}})
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "safety_summary_unavailable", "message": f"No se pudo leer el resumen de seguridad: {error}"},
        ) from error
