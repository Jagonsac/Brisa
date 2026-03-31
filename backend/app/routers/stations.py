from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from app.schemas.station import StationsResponse
from app.services.bicimad_service import BicimadService

router = APIRouter(prefix="/api/stations", tags=["stations"])
service = BicimadService()


@router.get("", response_model=StationsResponse)
async def get_stations(source: Literal["auto", "remote", "snapshot"] = Query(default="auto")) -> StationsResponse:
    try:
        return await service.get_stations(source_mode=source)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
