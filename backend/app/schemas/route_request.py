from typing import Literal

from pydantic import BaseModel, Field


class RouteRequest(BaseModel):
    originQuery: str = Field(min_length=1, max_length=180)
    destinationQuery: str = Field(min_length=1, max_length=180)
    mode: Literal["fastest", "safe", "balanced", "night"]
