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
        self.neighborhood_grid_path = self.data_dir / "madrid_safety_neighborhood_grid_v2.geojson"
        self.neighborhood_meta_path = self.data_dir / "safety_neighborhood_metadata_v2.json"
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

        for cell in features:
            neighborhood = self._resolve_neighborhood(cell.get("geometry"), neighborhoods)
            if neighborhood is None:
                continue

            props = cell.get("properties", {})
            safety_score = float(props.get("safetyScore", 0))
            risk_score = float(props.get("riskScore", 0))
            accidents = int(props.get("accidentCount", 0))

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
            bucket["weighted_safety"] += safety_score
            bucket["weighted_risk"] += risk_score
            bucket["accidents"] += accidents
            bucket["weight_total"] += 1
            bucket["cells_equivalent"] += 1

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
                            f"Score agregado por celda-centro en {cells_equivalent} celdas equivalentes.",
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

    def _resolve_neighborhood(self, cell_geometry: dict | None, neighborhoods: list):
        if not cell_geometry:
            return None

        try:
            cell_projected = self.neighborhood_service.project_geometry(cell_geometry)
        except Exception:
            return None

        if cell_projected.is_empty:
            return None

        centroid = cell_projected.centroid
        centroid_x, centroid_y = float(centroid.x), float(centroid.y)

        for neighborhood in neighborhoods:
            if not self._point_within_bbox(centroid_x, centroid_y, neighborhood.bounds_projected):
                continue
            if neighborhood.projected_geometry.contains(centroid):
                return neighborhood

        return self._nearest_neighborhood_projected(centroid_x, centroid_y, neighborhoods)

    @staticmethod
    def _point_within_bbox(x: float, y: float, bbox: tuple[float, float, float, float]) -> bool:
        return bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]

    @staticmethod
    def _nearest_neighborhood_projected(x: float, y: float, neighborhoods: list):
        nearest = None
        nearest_dist = None
        for neighborhood in neighborhoods:
            min_x, min_y, max_x, max_y = neighborhood.bounds_projected
            center_x = (min_x + max_x) / 2
            center_y = (min_y + max_y) / 2
            dist = (center_x - x) ** 2 + (center_y - y) ** 2
            if nearest_dist is None or dist < nearest_dist:
                nearest = neighborhood
                nearest_dist = dist
        return nearest

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
