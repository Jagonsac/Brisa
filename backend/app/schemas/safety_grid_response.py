from typing import Any

from pydantic import BaseModel


class SafetyGridMeta(BaseModel):
    version: str
    cellSizeMeters: int
    sources: dict[str, bool]
    trafficFallbackUsed: bool


class SafetyGridResponse(BaseModel):
    data: dict[str, Any]
    meta: SafetyGridMeta
