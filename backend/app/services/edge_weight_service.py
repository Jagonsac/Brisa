from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from app.core.routing_profiles import routing_profiles_config
from app.services.edge_safety_service import EdgeSafetyService


class EdgeWeightService:
    def __init__(self) -> None:
        self.edge_safety_service = EdgeSafetyService()
        self.cache_dir = Path(__file__).resolve().parents[2] / "data" / "routing"
        self.weights_path = self.cache_dir / f"edge_metrics_{routing_profiles_config.cache_version}.json"
        self.route_meta_path = self.cache_dir / f"route_metadata_{routing_profiles_config.cache_version}.json"
        self._lock = threading.Lock()
        self._cached: dict | None = None

    def get_edge_weights(self) -> dict:
        with self._lock:
            if self._cached is not None:
                return self._cached
            if self.weights_path.exists():
                self._cached = json.loads(self.weights_path.read_text(encoding="utf-8"))
                return self._cached

            payload = self._build_and_cache()
            self._cached = payload
            return payload

    def rebuild(self) -> dict:
        with self._lock:
            payload = self._build_and_cache()
            self._cached = payload
            return payload

    def _build_and_cache(self) -> dict:
        payload = self.edge_safety_service.build_edge_metrics()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.weights_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

        route_metadata = {
            "version": routing_profiles_config.cache_version,
            "updatedAt": datetime.now(timezone.utc).isoformat(),
            "weightConfig": {
                "fastestExtremeHostilityMultiplier": routing_profiles_config.fastest_extreme_hostility_multiplier,
                "safeRiskMultiplier": routing_profiles_config.safe_risk_multiplier,
                "balancedRiskMultiplier": routing_profiles_config.balanced_risk_multiplier,
                "nightBaseRiskMultiplier": routing_profiles_config.night_base_risk_multiplier,
                "nightLightingMultiplier": routing_profiles_config.night_lighting_multiplier,
                "nightAccidentMultiplier": routing_profiles_config.night_accident_multiplier,
            },
            "nightWindow": {
                "startHour": routing_profiles_config.night_start_hour,
                "endHour": routing_profiles_config.night_end_hour,
            },
            "edgeMetrics": payload.get("metadata", {}),
        }
        self.route_meta_path.write_text(json.dumps(route_metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload
