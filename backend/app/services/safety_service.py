from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from app.core.safety_config import safety_config
from app.services.neighborhood_service import NeighborhoodService
from app.services.safety_grid_builder import SafetyGridBuilder


class SafetyService:
    def __init__(self) -> None:
        self.builder = SafetyGridBuilder()
        self.neighborhood_service = NeighborhoodService()
        self.data_dir = Path(__file__).resolve().parents[2] / "data" / "safety" / "processed"
        self.grid_path = self.data_dir / "madrid_safety_grid_v1.geojson"
        self.meta_path = self.data_dir / "safety_metadata_v1.json"
        self.neighborhood_grid_path = self.data_dir / "madrid_safety_neighborhood_grid_v1.geojson"
        self.neighborhood_meta_path = self.data_dir / "safety_neighborhood_metadata_v1.json"
        self._lock = threading.Lock()
        self._cached_grid: dict | None = None
        self._cached_meta: dict | None = None
        self._cached_neighborhood_grid: dict | None = None
        self._cached_neighborhood_meta: dict | None = None

    def get_grid(self, bbox: tuple[float, float, float, float] | None = None) -> tuple[dict, dict]:
        collection, metadata = self._ensure_cached()
        if bbox is not None:
            collection = self._filter_collection_by_bbox(collection, bbox)
        return collection, metadata

    def get_neighborhood_grid(self, bbox: tuple[float, float, float, float] | None = None) -> tuple[dict, dict]:
        if bbox is None:
            return self._ensure_neighborhood_cached()

        grid_collection, metadata = self.get_grid(bbox)
        try:
            neighborhoods, neighborhood_meta = self.neighborhood_service.load_boundaries()
            neighborhood_scores = self._aggregate_cells_by_neighborhood(grid_collection, neighborhoods)
            collection = {"type": "FeatureCollection", "features": neighborhood_scores}
            merged_meta = {**metadata, "aggregationLevel": "neighborhood", "neighborhoods": neighborhood_meta}
            return collection, merged_meta
        except Exception as error:
            return self._fallback_to_cell_collection(grid_collection, metadata, str(error))

    def get_summary(self) -> dict:
        _, metadata = self._ensure_cached()
        return {
            "version": metadata.get("version", safety_config.version),
            "cellCount": metadata.get("cellCount", 0),
            "scoreMin": metadata.get("scoreMin", 0),
            "scoreMax": metadata.get("scoreMax", 0),
            "scoreAvg": metadata.get("scoreAvg", 0),
            "weights": metadata.get("weights", {}),
            "sources": metadata.get("sources", {}),
            "trafficFallbackUsed": metadata.get("trafficFallbackUsed", True),
            "updatedAt": metadata.get("updatedAt"),
        }

    def rebuild(self) -> tuple[dict, dict]:
        with self._lock:
            collection, metadata = self.builder.build()
            self.data_dir.mkdir(parents=True, exist_ok=True)
            metadata["updatedAt"] = self._iso_now()
            self.grid_path.write_text(json.dumps(collection, ensure_ascii=False), encoding="utf-8")
            self.meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
            self._cached_grid = collection
            self._cached_meta = metadata
            self._cached_neighborhood_grid = None
            self._cached_neighborhood_meta = None
            if self.neighborhood_grid_path.exists():
                self.neighborhood_grid_path.unlink()
            if self.neighborhood_meta_path.exists():
                self.neighborhood_meta_path.unlink()
            return collection, metadata

    def _aggregate_cells_by_neighborhood(self, grid_collection: dict, neighborhoods: list) -> list[dict]:
        buckets: dict[str, dict] = {}
        features = grid_collection.get("features", [])
        neighborhood_bounds = {item.neighborhood_id: self._geometry_bounds(item.geometry) for item in neighborhoods}

        for cell in features:
            ring = self._extract_ring(cell.get("geometry"))
            if not ring:
                continue
            memberships = self._resolve_memberships(ring, neighborhoods, neighborhood_bounds)
            if not memberships:
                continue

            props = cell.get("properties", {})
            safety_score = float(props.get("safetyScore", 0))
            risk_score = float(props.get("riskScore", 0))
            accidents = int(props.get("accidentCount", 0))

            for neighborhood, weight in memberships:
                if neighborhood.neighborhood_id not in buckets:
                    buckets[neighborhood.neighborhood_id] = {
                        "neighborhood": neighborhood,
                        "weighted_safety": 0.0,
                        "weighted_risk": 0.0,
                        "accidents": 0.0,
                        "weight_total": 0.0,
                        "cells_equivalent": 0.0,
                    }
                bucket = buckets[neighborhood.neighborhood_id]
                bucket["weighted_safety"] += safety_score * weight
                bucket["weighted_risk"] += risk_score * weight
                bucket["accidents"] += accidents * weight
                bucket["weight_total"] += weight
                bucket["cells_equivalent"] += weight

        aggregated = []
        for bucket in buckets.values():
            neighborhood = bucket["neighborhood"]
            total_weight = bucket["weight_total"]
            if total_weight <= 0:
                continue

            safety_score = int(round(bucket["weighted_safety"] / total_weight))
            risk_score = int(round(bucket["weighted_risk"] / total_weight))
            accidents = int(round(bucket["accidents"]))
            cells_equivalent = round(bucket["cells_equivalent"], 2)
            aggregated.append(
                {
                    "type": "Feature",
                    "geometry": neighborhood.geometry,
                    "properties": {
                        "neighborhoodId": neighborhood.neighborhood_id,
                        "name": neighborhood.name,
                        "district": neighborhood.district,
                        "safetyScore": max(0, min(100, safety_score)),
                        "riskScore": max(0, min(100, risk_score)),
                        "accidentCount": max(0, accidents),
                        "cellCount": cells_equivalent,
                        "explanation": [
                            f"Score agregado por ponderación espacial de {cells_equivalent} celdas equivalentes.",
                            f"Accidentes ciclistas estimados en el área: {max(0, accidents)}.",
                        ],
                    },
                }
            )

        return aggregated

    def _ensure_cached(self) -> tuple[dict, dict]:
        with self._lock:
            if self._cached_grid is not None and self._cached_meta is not None:
                return self._cached_grid, self._cached_meta

            if self.grid_path.exists() and self.meta_path.exists():
                collection = json.loads(self.grid_path.read_text(encoding="utf-8"))
                metadata = json.loads(self.meta_path.read_text(encoding="utf-8"))
                self._cached_grid = collection
                self._cached_meta = metadata
                return collection, metadata

        return self.rebuild()

    def _ensure_neighborhood_cached(self) -> tuple[dict, dict]:
        with self._lock:
            if self._cached_neighborhood_grid is not None and self._cached_neighborhood_meta is not None:
                return self._cached_neighborhood_grid, self._cached_neighborhood_meta

            if self.neighborhood_grid_path.exists() and self.neighborhood_meta_path.exists():
                collection = json.loads(self.neighborhood_grid_path.read_text(encoding="utf-8"))
                metadata = json.loads(self.neighborhood_meta_path.read_text(encoding="utf-8"))
                self._cached_neighborhood_grid = collection
                self._cached_neighborhood_meta = metadata
                return collection, metadata

        grid_collection, metadata = self._ensure_cached()
        try:
            neighborhoods, neighborhood_meta = self.neighborhood_service.load_boundaries()
            neighborhood_scores = self._aggregate_cells_by_neighborhood(grid_collection, neighborhoods)
            collection = {"type": "FeatureCollection", "features": neighborhood_scores}
            merged_meta = {**metadata, "aggregationLevel": "neighborhood", "neighborhoods": neighborhood_meta}
        except Exception as error:
            collection, merged_meta = self._fallback_to_cell_collection(grid_collection, metadata, str(error))

        with self._lock:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.neighborhood_grid_path.write_text(json.dumps(collection, ensure_ascii=False), encoding="utf-8")
            self.neighborhood_meta_path.write_text(json.dumps(merged_meta, ensure_ascii=False, indent=2), encoding="utf-8")
            self._cached_neighborhood_grid = collection
            self._cached_neighborhood_meta = merged_meta

        return collection, merged_meta

    def _fallback_to_cell_collection(self, grid_collection: dict, metadata: dict, reason: str) -> tuple[dict, dict]:
        merged_meta = {
            **metadata,
            "aggregationLevel": "cell",
            "neighborhoods": {"source": "fallback", "warning": reason},
        }
        return grid_collection, merged_meta

    def _resolve_memberships(self, ring: list[list[float]], neighborhoods: list, bounds: dict[str, tuple[float, float, float, float]]) -> list[tuple[Any, float]]:
        sample_points = self._sample_points(ring)
        scores: dict[str, tuple[Any, int]] = {}

        for neighborhood in neighborhoods:
            hits = 0
            for lon, lat in sample_points:
                if self.neighborhood_service.contains(neighborhood.geometry, lon, lat):
                    hits += 1
            if hits > 0:
                scores[neighborhood.neighborhood_id] = (neighborhood, hits)

        if not scores:
            centroid = self._centroid(ring)
            nearest = self._nearest_neighborhood(centroid[0], centroid[1], neighborhoods, bounds)
            if nearest is None:
                return []
            return [(nearest, 1.0)]

        total_hits = sum(item[1] for item in scores.values()) or 1
        return [(item[0], item[1] / total_hits) for item in scores.values()]

    @staticmethod
    def _extract_ring(geometry: dict | None) -> list[list[float]]:
        if not geometry:
            return []
        if geometry.get("type") != "Polygon":
            return []
        coordinates = geometry.get("coordinates", [])
        if not coordinates or not isinstance(coordinates[0], list):
            return []
        ring = coordinates[0]
        if len(ring) < 4:
            return []
        return [point for point in ring if isinstance(point, list) and len(point) >= 2]

    @staticmethod
    def _centroid(ring: list[list[float]]) -> tuple[float, float]:
        points = ring[:-1] if len(ring) > 1 else ring
        count = max(len(points), 1)
        lon = sum(float(point[0]) for point in points) / count
        lat = sum(float(point[1]) for point in points) / count
        return lon, lat

    def _sample_points(self, ring: list[list[float]]) -> list[tuple[float, float]]:
        min_lon, min_lat, max_lon, max_lat = self._ring_bounds(ring)
        center_lon, center_lat = self._centroid(ring)
        return [
            (center_lon, center_lat),
            (min_lon, min_lat),
            (max_lon, min_lat),
            (max_lon, max_lat),
            (min_lon, max_lat),
            ((min_lon + center_lon) / 2, center_lat),
            ((max_lon + center_lon) / 2, center_lat),
            (center_lon, (min_lat + center_lat) / 2),
            (center_lon, (max_lat + center_lat) / 2),
        ]

    @staticmethod
    def _ring_bounds(ring: list[list[float]]) -> tuple[float, float, float, float]:
        lons = [float(point[0]) for point in ring]
        lats = [float(point[1]) for point in ring]
        return min(lons), min(lats), max(lons), max(lats)

    def _nearest_neighborhood(self, lon: float, lat: float, neighborhoods: list, bounds: dict[str, tuple[float, float, float, float]]):
        nearest = None
        nearest_dist = None
        for neighborhood in neighborhoods:
            bbox = bounds.get(neighborhood.neighborhood_id)
            if bbox is None:
                continue
            min_lon, min_lat, max_lon, max_lat = bbox
            center_lon = (min_lon + max_lon) / 2
            center_lat = (min_lat + max_lat) / 2
            dist = (center_lon - lon) ** 2 + (center_lat - lat) ** 2
            if nearest_dist is None or dist < nearest_dist:
                nearest = neighborhood
                nearest_dist = dist
        return nearest

    def _geometry_bounds(self, geometry: dict) -> tuple[float, float, float, float] | None:
        geometry_type = geometry.get("type")
        coordinates = geometry.get("coordinates", [])
        points: list[tuple[float, float]] = []
        if geometry_type == "Polygon":
            for ring in coordinates:
                for point in ring:
                    if isinstance(point, list) and len(point) >= 2:
                        points.append((float(point[0]), float(point[1])))
        elif geometry_type == "MultiPolygon":
            for polygon in coordinates:
                for ring in polygon:
                    for point in ring:
                        if isinstance(point, list) and len(point) >= 2:
                            points.append((float(point[0]), float(point[1])))
        if not points:
            return None
        lons = [item[0] for item in points]
        lats = [item[1] for item in points]
        return min(lons), min(lats), max(lons), max(lats)

    @staticmethod
    def _filter_collection_by_bbox(collection: dict, bbox: tuple[float, float, float, float]) -> dict:
        min_lon, min_lat, max_lon, max_lat = bbox
        features = []
        for feature in collection.get("features", []):
            coords = feature.get("geometry", {}).get("coordinates", [[]])[0]
            if not coords:
                continue
            lons = [point[0] for point in coords]
            lats = [point[1] for point in coords]
            if max(lons) < min_lon or min(lons) > max_lon or max(lats) < min_lat or min(lats) > max_lat:
                continue
            features.append(feature)
        return {"type": "FeatureCollection", "features": features}

    @staticmethod
    def _iso_now() -> str:
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()
