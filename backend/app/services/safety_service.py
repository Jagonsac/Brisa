from __future__ import annotations

import json
import threading
from pathlib import Path

from app.core.safety_config import safety_config
from app.services.safety_grid_builder import SafetyGridBuilder


class SafetyService:
    def __init__(self) -> None:
        self.builder = SafetyGridBuilder()
        self.data_dir = Path(__file__).resolve().parents[2] / "data" / "safety" / "processed"
        self.grid_path = self.data_dir / "madrid_safety_grid_v1.geojson"
        self.meta_path = self.data_dir / "safety_metadata_v1.json"
        self._lock = threading.Lock()

    def get_grid(self, bbox: tuple[float, float, float, float] | None = None) -> tuple[dict, dict]:
        collection, metadata = self._ensure_cached()
        if bbox is not None:
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
            collection = {"type": "FeatureCollection", "features": features}
        return collection, metadata

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
            return collection, metadata

    def _ensure_cached(self) -> tuple[dict, dict]:
        with self._lock:
            if self.grid_path.exists() and self.meta_path.exists():
                collection = json.loads(self.grid_path.read_text(encoding="utf-8"))
                metadata = json.loads(self.meta_path.read_text(encoding="utf-8"))
                return collection, metadata

        return self.rebuild()

    @staticmethod
    def _iso_now() -> str:
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()
