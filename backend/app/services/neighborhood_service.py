from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from pyproj import Transformer
from shapely.geometry import Point, shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform as shapely_transform

from app.core.safety_config import safety_config


@dataclass
class NeighborhoodArea:
    neighborhood_id: str
    name: str
    district: str
    geometry: dict
    projected_geometry: BaseGeometry
    bounds_projected: tuple[float, float, float, float]


class NeighborhoodService:
    def __init__(self) -> None:
        self.raw_dir = Path(__file__).resolve().parents[2] / "data" / "safety" / "raw"
        self.local_boundaries_path = self.raw_dir / "madrid_barrios_131.geojson"
        self.boundaries_path = self.raw_dir / safety_config.neighborhoods_cache_filename
        self.to_projected = Transformer.from_crs(safety_config.target_crs, safety_config.projected_crs, always_xy=True)
        self._cached_boundaries: tuple[list[NeighborhoodArea], dict] | None = None

    def load_boundaries(self) -> tuple[list[NeighborhoodArea], dict]:
        if self._cached_boundaries is not None:
            return self._cached_boundaries

        payload, source = self._load_geojson_payload()
        features = payload.get("features", [])
        neighborhoods: list[NeighborhoodArea] = []

        for index, feature in enumerate(features):
            geometry = feature.get("geometry")
            if not geometry or geometry.get("type") not in {"Polygon", "MultiPolygon"}:
                continue

            props = feature.get("properties", {})
            code = str(props.get("COD_BAR") or props.get("CodigoBarrio") or props.get("codigo_barrio") or "").strip()
            neighborhood_id = code or f"madrid-barrio-{index + 1:03d}"
            name = str(props.get("NOMBRE") or props.get("BARRIO_MAY") or props.get("BARRIO") or props.get("name") or neighborhood_id)
            district = str(props.get("NOMDIS") or props.get("DISTRITO") or props.get("district") or "")

            polygon = shape(geometry)
            projected = shapely_transform(self.to_projected.transform, polygon)
            if projected.is_empty or projected.area <= 0:
                continue

            neighborhoods.append(
                NeighborhoodArea(
                    neighborhood_id=neighborhood_id,
                    name=name.strip(),
                    district=district.strip(),
                    geometry=geometry,
                    projected_geometry=projected,
                    bounds_projected=projected.bounds,
                )
            )

        metadata = {
            "source": source,
            "neighborhoodCount": len(neighborhoods),
            "url": safety_config.neighborhoods_geojson_url,
        }
        self._cached_boundaries = (neighborhoods, metadata)
        return self._cached_boundaries

    def _load_geojson_payload(self) -> tuple[dict[str, Any], str]:
        if self.local_boundaries_path.exists():
            payload = json.loads(self.local_boundaries_path.read_text(encoding="utf-8"))
            if self._is_valid_geojson(payload):
                return payload, f"local:{self.local_boundaries_path.name}"

        if self.boundaries_path.exists():
            cached_payload = json.loads(self.boundaries_path.read_text(encoding="utf-8"))
            if self._is_valid_geojson(cached_payload):
                return cached_payload, "cache"

        self.raw_dir.mkdir(parents=True, exist_ok=True)
        urls = [safety_config.neighborhoods_geojson_url, *safety_config.neighborhoods_geojson_fallback_urls]
        errors: list[str] = []
        for url in urls:
            request = Request(url, headers={"User-Agent": "Brisa/0.1 (safety neighborhoods)"})
            try:
                with urlopen(request, timeout=safety_config.download_timeout_seconds) as response:
                    raw_bytes = response.read()
                payload = json.loads(raw_bytes.decode("utf-8", errors="ignore"))
                if not self._is_valid_geojson(payload):
                    errors.append(f"{url}: GeoJSON inválido o sin features")
                    continue
                self.boundaries_path.write_bytes(raw_bytes)
                return payload, f"download:{url}"
            except Exception as error:
                errors.append(f"{url}: {error}")

        if self.boundaries_path.exists():
            cached_payload = json.loads(self.boundaries_path.read_text(encoding="utf-8"))
            if self._is_valid_geojson(cached_payload):
                return cached_payload, "cache-stale"

        joined_errors = " | ".join(errors) if errors else "Sin detalles"
        raise RuntimeError(f"No se pudo cargar GeoJSON de barrios. Errores: {joined_errors}")

    @staticmethod
    def _is_valid_geojson(payload: dict) -> bool:
        if payload.get("type") != "FeatureCollection":
            return False
        features = payload.get("features", [])
        if not isinstance(features, list) or not features:
            return False
        return any((feature.get("geometry", {}) or {}).get("type") in {"Polygon", "MultiPolygon"} for feature in features if isinstance(feature, dict))

    def project_geometry(self, geometry: dict) -> BaseGeometry:
        raw_geometry = shape(geometry)
        return shapely_transform(self.to_projected.transform, raw_geometry)

    def resolve_neighborhood_projected_point(
        self,
        x: float,
        y: float,
        neighborhoods: list[NeighborhoodArea],
    ) -> NeighborhoodArea | None:
        point = Point(float(x), float(y))
        for neighborhood in neighborhoods:
            if not self._point_within_bbox(float(x), float(y), neighborhood.bounds_projected):
                continue
            if neighborhood.projected_geometry.covers(point):
                return neighborhood
        return self.nearest_neighborhood_projected(float(x), float(y), neighborhoods)

    def nearest_neighborhood_projected(
        self,
        x: float,
        y: float,
        neighborhoods: list[NeighborhoodArea],
    ) -> NeighborhoodArea | None:
        point = Point(float(x), float(y))
        nearest: NeighborhoodArea | None = None
        nearest_dist: float | None = None
        for neighborhood in neighborhoods:
            dist = float(neighborhood.projected_geometry.distance(point))
            if nearest_dist is None or dist < nearest_dist:
                nearest = neighborhood
                nearest_dist = dist
        return nearest

    @staticmethod
    def _point_within_bbox(x: float, y: float, bbox: tuple[float, float, float, float]) -> bool:
        return bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]

    # Compat alias para código previo que aún invoque el método privado.
    def _nearest_neighborhood_projected(
        self,
        x: float,
        y: float,
        neighborhoods: list[NeighborhoodArea],
    ) -> NeighborhoodArea | None:
        return self.nearest_neighborhood_projected(x, y, neighborhoods)
