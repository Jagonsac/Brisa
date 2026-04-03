from fastapi import APIRouter, HTTPException, Query, status

from app.services.cyclability_service import CyclabilityService

router = APIRouter(prefix="/api/cyclability", tags=["cyclability"])
service = CyclabilityService()


@router.get("/neighborhoods")
def get_cyclability_neighborhoods() -> dict:
    try:
        return service.list_neighborhoods()
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "cyclability_unavailable", "message": f"No se pudo cargar el índice de ciclabilidad: {error}"},
        ) from error


@router.get("/neighborhoods/geojson")
def get_cyclability_neighborhoods_geojson() -> dict:
    try:
        return service.get_geojson()
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "cyclability_geojson_unavailable", "message": f"No se pudo cargar el GeoJSON de ciclabilidad: {error}"},
        ) from error


@router.get("/neighborhoods/compare")
def compare_neighborhoods(left: str = Query(...), right: str = Query(...)) -> dict:
    try:
        return service.compare(left, right)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "neighborhood_not_found", "message": "Barrio no encontrado para comparar."})
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "cyclability_compare_unavailable", "message": f"No se pudo comparar barrios: {error}"},
        ) from error


@router.get("/neighborhoods/{neighborhood_id}")
def get_cyclability_neighborhood(neighborhood_id: str) -> dict:
    try:
        return service.get_neighborhood_detail(neighborhood_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "neighborhood_not_found", "message": "Barrio no encontrado."})
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "cyclability_detail_unavailable", "message": f"No se pudo cargar el detalle del barrio: {error}"},
        ) from error
