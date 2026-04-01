from __future__ import annotations

import json
import threading
from pathlib import Path

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
        neighborhoods, neighborhood_meta = self.neighborhood_service.load_boundaries()
        neighborhood_scores = self._aggregate_cells_by_neighborhood(grid_collection, neighborhoods)
        collection = {"type": "FeatureCollection", "features": neighborhood_scores}
        merged_meta = {**metadata, "aggregationLevel": "neighborhood", "neighborhoods": neighborhood_meta}
        return collection, merged_meta

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

        for cell in features:
            coordinates = cell.get("geometry", {}).get("coordinates", [])
            if not coordinates or not coordinates[0]:
                continue
            ring = coordinates[0]
            centroid_lon = sum(point[0] for point in ring[:-1]) / max(len(ring) - 1, 1)
            centroid_lat = sum(point[1] for point in ring[:-1]) / max(len(ring) - 1, 1)

            target = None
            for neighborhood in neighborhoods:
                if self.neighborhood_service.contains(neighborhood.geometry, centroid_lon, centroid_lat):
                    target = neighborhood
                    break
            if target is None:
                continue

            if target.neighborhood_id not in buckets:
                buckets[target.neighborhood_id] = {
                    "neighborhood": target,
                    "safety_scores": [],
                    "risk_scores": [],
                    "accidents": 0,
                    "cells": 0,
                }

            bucket = buckets[target.neighborhood_id]
            props = cell.get("properties", {})
            bucket["safety_scores"].append(float(props.get("safetyScore", 0)))
            bucket["risk_scores"].append(float(props.get("riskScore", 0)))
            bucket["accidents"] += int(props.get("accidentCount", 0))
            bucket["cells"] += 1

        aggregated = []
        for bucket in buckets.values():
            neighborhood = bucket["neighborhood"]
            safety_scores = bucket["safety_scores"]
            risk_scores = bucket["risk_scores"]
            if not safety_scores:
                continue

            safety_score = int(round(sum(safety_scores) / len(safety_scores)))
            risk_score = int(round(sum(risk_scores) / len(risk_scores)))
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
                        "accidentCount": bucket["accidents"],
                        "cellCount": bucket["cells"],
                        "explanation": [
                            f"Score agregado a partir de {bucket['cells']} celdas de seguridad.",
                            f"Accidentes ciclistas registrados en el área: {bucket['accidents']}.",
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
        neighborhoods, neighborhood_meta = self.neighborhood_service.load_boundaries()
        neighborhood_scores = self._aggregate_cells_by_neighborhood(grid_collection, neighborhoods)
        collection = {"type": "FeatureCollection", "features": neighborhood_scores}
        merged_meta = {**metadata, "aggregationLevel": "neighborhood", "neighborhoods": neighborhood_meta}

        with self._lock:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.neighborhood_grid_path.write_text(json.dumps(collection, ensure_ascii=False), encoding="utf-8")
            self.neighborhood_meta_path.write_text(json.dumps(merged_meta, ensure_ascii=False, indent=2), encoding="utf-8")
            self._cached_neighborhood_grid = collection
            self._cached_neighborhood_meta = merged_meta

        return collection, merged_meta

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
