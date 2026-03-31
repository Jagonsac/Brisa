from typing import Literal

from pydantic import BaseModel


class Station(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    address: str | None = None
    capacity: float | None = None


class StationsMeta(BaseModel):
    count: int
    source: Literal["gbfs-station-information", "emt-geojson-fallback", "local-snapshot-fallback"]
    fallbackUsed: bool
    warnings: list[str] = []


class StationsResponse(BaseModel):
    data: list[Station]
    meta: StationsMeta
