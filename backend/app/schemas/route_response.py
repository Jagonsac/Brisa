from typing import Literal

from pydantic import BaseModel


class RouteFeatureGeometry(BaseModel):
    type: Literal["LineString"] = "LineString"
    coordinates: list[list[float]]


class RouteFeatureProperties(BaseModel):
    distanceMeters: float
    mode: Literal["fastest", "safe", "balanced", "night", "walk", "bicimad"]
    profile: str | None = None


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
    mode: Literal["fastest", "safe", "balanced", "night", "bicimad"]
    relativeSafety: Literal["high", "medium", "low"]
    lightingQuality: Literal["high", "medium", "low"]
    nightRisk: Literal["low", "medium", "high"]
    estimatedDurationMinutes: float | None = None
    totalDurationSeconds: float | None = None
    walkDistanceMeters: float | None = None
    walkDurationSeconds: float | None = None
    bikeDistanceMeters: float | None = None
    bikeDurationSeconds: float | None = None




class RouteHazardPoint(BaseModel):
    lat: float
    lon: float
    riskType: Literal["dangerous_junction", "bike_accident_hotspot", "low_cyclability_neighborhood"]
    severity: Literal["medium", "high"]
    title: str
    description: str
    evidence: dict
    routePosition: dict

class RouteData(BaseModel):
    routeGeoJson: RouteGeoJsonFeature
    origin: RouteLocation
    destination: RouteLocation
    summary: RouteSummary
    explanations: list[str]
    hazardPoints: list[RouteHazardPoint] = []
    segments: list[dict] | None = None
    stations: dict | None = None
    bikeProfile: Literal["fastest", "safe", "balanced", "night"] | None = None
    transportMode: Literal["bike", "bicimad"] = "bike"


class RouteMeta(BaseModel):
    engine: Literal["osmnx"] = "osmnx"
    graphSource: Literal["cache", "download"]
    weightProfile: Literal["fastest", "safe", "balanced", "night"]
    usedSafetyGrid: bool
    usedLightingGrid: bool
    usedNightRiskGrid: bool
    networkType: str
    liveStatusUsed: bool | None = None
    fallbackUsed: bool | None = None
    evaluatedPairs: int | None = None
    discardedPairs: int | None = None


class RouteResponse(BaseModel):
    data: RouteData
    meta: RouteMeta
