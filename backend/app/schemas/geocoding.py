from pydantic import BaseModel


class SuggestionItem(BaseModel):
    label: str
    value: str
    lat: float
    lon: float


class SuggestMeta(BaseModel):
    count: int


class GeocodingSuggestResponse(BaseModel):
    data: list[SuggestionItem]
    meta: SuggestMeta
