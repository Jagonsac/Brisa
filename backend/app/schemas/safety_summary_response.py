from pydantic import BaseModel


class SafetySummaryData(BaseModel):
    version: str
    cellCount: int
    scoreMin: int
    scoreMax: int
    scoreAvg: float
    weights: dict[str, float]
    sources: dict[str, bool]
    trafficFallbackUsed: bool
    updatedAt: str | None = None


class SafetySummaryMeta(BaseModel):
    ready: bool


class SafetySummaryResponse(BaseModel):
    data: SafetySummaryData
    meta: SafetySummaryMeta
