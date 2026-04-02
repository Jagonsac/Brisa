from typing import Literal

from pydantic import BaseModel


class RouteFeatureGeometry(BaseModel):
    type: Literal["LineString"] = "LineString"
    coordinates: list[list[float]]


class RouteFeatureProperties(BaseModel):
    distanceMeters: float
    mode: Literal["fastest", "safe", "balanced", "night"]
    profile: str


class RouteGeoJsonFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: RouteFeatureGeometry
    properties: RouteFeatureProperties


class RouteLocation(BaseModel):
    query: str
    displayName: str
    lat: float
    lon: float


class RouteSummary(BaseModel):
    distanceMeters: float
    distanceKm: float
    mode: Literal["fastest", "safe", "balanced", "night"]
    relativeSafety: Literal["high", "medium", "low"]
    lightingQuality: Literal["high", "medium", "low"]
    nightRisk: Literal["low", "medium", "high"]


class RouteData(BaseModel):
    routeGeoJson: RouteGeoJsonFeature
    origin: RouteLocation
    destination: RouteLocation
    summary: RouteSummary
    explanations: list[str]


class RouteMeta(BaseModel):
    engine: Literal["osmnx"] = "osmnx"
    graphSource: Literal["cache", "download"]
    weightProfile: Literal["fastest", "safe", "balanced", "night"]
    usedSafetyGrid: bool
    usedLightingGrid: bool
    usedNightRiskGrid: bool
    networkType: str


class RouteResponse(BaseModel):
    data: RouteData
    meta: RouteMeta
