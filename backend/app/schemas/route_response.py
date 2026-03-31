from typing import Literal

from pydantic import BaseModel


class RouteFeatureGeometry(BaseModel):
    type: Literal["LineString"] = "LineString"
    coordinates: list[list[float]]


class RouteFeatureProperties(BaseModel):
    distanceMeters: float
    mode: str
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


class RouteData(BaseModel):
    routeGeoJson: RouteGeoJsonFeature
    origin: RouteLocation
    destination: RouteLocation
    summary: RouteSummary


class RouteMeta(BaseModel):
    source: Literal["osmnx"] = "osmnx"
    graphSource: Literal["cache", "download"]
    weight: Literal["length"] = "length"
    networkType: str


class RouteResponse(BaseModel):
    data: RouteData
    meta: RouteMeta
