from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from app.services.cyclability_service import CyclabilityService
from app.services.route_service import RouteService
from app.services.safety_service import SafetyService


@dataclass(frozen=True)
class BootstrapResult:
    rebuilt_routing: bool
    rebuilt_safety: bool
    rebuilt_cyclability: bool


class BootstrapService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.route_service = RouteService()
        self.safety_service = SafetyService()
        self.cyclability_service = CyclabilityService()
        self.data_root = Path(__file__).resolve().parents[2] / "data"
        self.state_path = self.data_root / "cache" / "bootstrap_state_v1.json"

    def warmup(self, *, force_rebuild: bool = False) -> BootstrapResult:
        self.route_service.warmup_routing_engine()

        routing_ready = self.route_service.edge_weight_service.weights_path.exists()
        safety_ready = self.safety_service.grid_path.exists() and self.safety_service.meta_path.exists()
        neighborhood_safety_ready = (
            self.safety_service.neighborhood_grid_path.exists() and self.safety_service.neighborhood_meta_path.exists()
        )
        cyclability_ready = (
            self.cyclability_service.scores_path.exists()
            and self.cyclability_service.geojson_path.exists()
            and self.cyclability_service.metadata_path.exists()
        )

        state = self._read_state()
        current_fingerprint = self._build_fingerprint()
        same_fingerprint = state.get("fingerprint") == current_fingerprint

        rebuilt_routing = force_rebuild or not routing_ready or not same_fingerprint
        rebuilt_safety = force_rebuild or not safety_ready or not neighborhood_safety_ready or not same_fingerprint
        rebuilt_cyclability = force_rebuild or not cyclability_ready or not same_fingerprint

        if rebuilt_routing:
            self.route_service.edge_weight_service.rebuild()
        if rebuilt_safety:
            self.safety_service.rebuild()
            self.safety_service.get_neighborhood_grid()
        if rebuilt_cyclability:
            self.cyclability_service.rebuild()

        self._write_state(current_fingerprint)
        self.logger.info(
            "bootstrap_completed",
            extra={
                "rebuiltRouting": rebuilt_routing,
                "rebuiltSafety": rebuilt_safety,
                "rebuiltCyclability": rebuilt_cyclability,
                "forceRebuild": force_rebuild,
            },
        )
        return BootstrapResult(rebuilt_routing, rebuilt_safety, rebuilt_cyclability)

    def _build_fingerprint(self) -> dict:
        return {
            "routing_cache_version": self.route_service.edge_weight_service.weights_path.name,
            "graph_filename": self.route_service.graph_service.graph_path.name,
            "safety_grid": self.safety_service.grid_path.name,
            "neighborhood_safety_grid": self.safety_service.neighborhood_grid_path.name,
            "cyclability_version": "v1",
        }

    def _read_state(self) -> dict:
        if not self.state_path.exists():
            return {}
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _write_state(self, fingerprint: dict) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps({"fingerprint": fingerprint}, ensure_ascii=False, indent=2), encoding="utf-8")
