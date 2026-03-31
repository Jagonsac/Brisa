from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class RoutePointRequest(BaseModel):
    query: str = Field(min_length=1, max_length=180)
    lat: float | None = None
    lon: float | None = None

    @model_validator(mode="before")
    @classmethod
    def coerce_query(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        query = data.get("query")
        if query is None:
            return data

        parsed_query = str(query).strip()
        data["query"] = parsed_query
        return data

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

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_payload(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        normalized = dict(data)

        origin = normalized.get("origin")
        if not isinstance(origin, dict):
            origin_query = normalized.get("originQuery")
            if origin_query is not None:
                normalized["origin"] = {"query": origin_query}

        destination = normalized.get("destination")
        if not isinstance(destination, dict):
            destination_query = normalized.get("destinationQuery")
            if destination_query is not None:
                normalized["destination"] = {"query": destination_query}

        return normalized

    @model_validator(mode="after")
    def validate_business_fields(self) -> "RouteRequest":
        if self.origin.query.strip() == "" or self.destination.query.strip() == "":
            raise ValueError("origin.query y destination.query son obligatorios.")
        return self
