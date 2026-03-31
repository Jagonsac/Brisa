from typing import Literal

from pydantic import BaseModel, Field, model_validator


class RoutePointRequest(BaseModel):
    query: str = Field(min_length=1, max_length=180)
    lat: float | None = None
    lon: float | None = None

    @model_validator(mode="after")
    def validate_coordinate_pair(self) -> "RoutePointRequest":
        has_lat = self.lat is not None
        has_lon = self.lon is not None
        if has_lat != has_lon:
            raise ValueError("lat y lon deben enviarse juntos.")
        return self


class RouteRequest(BaseModel):
    origin: RoutePointRequest
    destination: RoutePointRequest
    mode: Literal["fastest", "safe", "balanced", "night"]
