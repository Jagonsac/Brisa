from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from pyproj import Transformer

from app.core.routing_profiles import routing_profiles_config
from app.core.safety_config import safety_config
from app.services.graph_service import GraphService
from app.services.lighting_service import LightingService
from app.services.night_risk_service import NightRiskService
from app.services.safety_service import SafetyService


class GridLookup:
    def __init__(self, values_by_cell: dict[tuple[int, int], float], *, min_x: float, min_y: float, cell_size: float, default_value: float) -> None:
        self.values_by_cell = values_by_cell
        self.min_x = min_x
        self.min_y = min_y
        self.cell_size = cell_size
        self.default_value = default_value

    def value_at(self, x: float, y: float) -> float:
        col = int((x - self.min_x) // self.cell_size)
        row = int((y - self.min_y) // self.cell_size)
        return float(self.values_by_cell.get((col, row), self.default_value))


class EdgeWeightService:
    def __init__(self) -> None:
        self.graph_service = GraphService()
        self.safety_service = SafetyService()
        self.lighting_service = LightingService()
        self.night_risk_service = NightRiskService()
        self.to_projected = Transformer.from_crs(safety_config.target_crs, safety_config.projected_crs, always_xy=True)
        self.cache_dir = Path(__file__).resolve().parents[2] / "data" / "routing"
        self.lighting_grid_path = self.cache_dir / f"lighting_grid_{routing_profiles_config.cache_version}.geojson"
        self.lighting_meta_path = self.cache_dir / f"lighting_metadata_{routing_profiles_config.cache_version}.json"
        self.night_grid_path = self.cache_dir / f"night_risk_grid_{routing_profiles_config.cache_version}.geojson"
        self.night_meta_path = self.cache_dir / f"night_risk_metadata_{routing_profiles_config.cache_version}.json"
        self.weights_path = self.cache_dir / f"edge_weights_{routing_profiles_config.cache_version}.json"
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

            payload = self._build()
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.weights_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            self._cached = payload
            return payload

    def _build(self) -> dict:
        graph, _ = self.graph_service.get_graph()
        safety_grid, safety_meta = self.safety_service.get_grid()
        lighting_grid, lighting_meta = self._load_or_build_lighting_grid()
        night_grid, night_meta = self._load_or_build_night_grid()

        safety_lookup = self._build_lookup(
            safety_grid,
            value_key="riskScore",
            to_unit=lambda value: max(0.0, min(1.0, value / 100)),
            fallback=0.45,
        )
        lighting_lookup = self._build_lookup(
            lighting_grid,
            value_key="lightingDeficit",
            to_unit=lambda value: max(0.0, min(1.0, value)),
            fallback=0.5,
        )
        night_lookup = self._build_lookup(
            night_grid,
            value_key="nightRisk",
            to_unit=lambda value: max(0.0, min(1.0, value)),
            fallback=0.35,
        )

        edges: dict[str, dict] = {}
        for u, v, key, data in graph.edges(keys=True, data=True):
            sample_points = self._sample_points(graph, u, v, data)
            if not sample_points:
                continue
            safety = self._avg_metric(safety_lookup, sample_points)
            lighting_deficit = self._avg_metric(lighting_lookup, sample_points)
            night_risk = self._avg_metric(night_lookup, sample_points)
            edge_id = f"{u}:{v}:{key}"
            edges[edge_id] = {
                "safetyRiskNormalized": round(safety, 6),
                "lightingDeficitNormalized": round(lighting_deficit, 6),
                "nightRiskNormalized": round(night_risk, 6),
            }

        route_metadata = {
            "version": routing_profiles_config.cache_version,
            "updatedAt": datetime.now(timezone.utc).isoformat(),
            "weightConfig": {
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
            "safetyGrid": safety_meta,
            "lightingGrid": lighting_meta,
            "nightRiskGrid": night_meta,
            "edgeCount": len(edges),
            "fallbacks": {
                "safetyRisk": safety_lookup.default_value,
                "lightingDeficit": lighting_lookup.default_value,
                "nightRisk": night_lookup.default_value,
            },
        }
        self.route_meta_path.write_text(json.dumps(route_metadata, ensure_ascii=False, indent=2), encoding="utf-8")

        return {
            "version": routing_profiles_config.cache_version,
            "edges": edges,
        }

    def _load_or_build_lighting_grid(self) -> tuple[dict, dict]:
        if self.lighting_grid_path.exists() and self.lighting_meta_path.exists():
            return (
                json.loads(self.lighting_grid_path.read_text(encoding="utf-8")),
                json.loads(self.lighting_meta_path.read_text(encoding="utf-8")),
            )

        collection, meta = self.lighting_service.build_lighting_grid()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.lighting_grid_path.write_text(json.dumps(collection, ensure_ascii=False), encoding="utf-8")
        self.lighting_meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        return collection, meta

    def _load_or_build_night_grid(self) -> tuple[dict, dict]:
        if self.night_grid_path.exists() and self.night_meta_path.exists():
            return (
                json.loads(self.night_grid_path.read_text(encoding="utf-8")),
                json.loads(self.night_meta_path.read_text(encoding="utf-8")),
            )

        collection, meta = self.night_risk_service.build_night_risk_grid()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.night_grid_path.write_text(json.dumps(collection, ensure_ascii=False), encoding="utf-8")
        self.night_meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        return collection, meta

    def _build_lookup(self, grid: dict, *, value_key: str, to_unit, fallback: float) -> GridLookup:
        features = grid.get("features", [])
        if not features:
            return GridLookup({}, min_x=0, min_y=0, cell_size=safety_config.cell_size_meters, default_value=fallback)

        cells = []
        for feature in features:
            coords = feature.get("geometry", {}).get("coordinates", [[]])[0]
            if not coords:
                continue
            projected = [self.to_projected.transform(float(lon), float(lat)) for lon, lat in coords]
            xs = [point[0] for point in projected]
            ys = [point[1] for point in projected]
            value = feature.get("properties", {}).get(value_key)
            try:
                normalized_value = to_unit(float(value))
            except (TypeError, ValueError):
                continue
            cells.append((min(xs), min(ys), normalized_value))

        if not cells:
            return GridLookup({}, min_x=0, min_y=0, cell_size=safety_config.cell_size_meters, default_value=fallback)

        min_x = min(cell[0] for cell in cells)
        min_y = min(cell[1] for cell in cells)
        lookup: dict[tuple[int, int], float] = {}
        for cell_x, cell_y, value in cells:
            col = int(round((cell_x - min_x) / safety_config.cell_size_meters))
            row = int(round((cell_y - min_y) / safety_config.cell_size_meters))
            lookup[(col, row)] = value

        avg_value = sum(lookup.values()) / len(lookup) if lookup else fallback
        return GridLookup(lookup, min_x=min_x, min_y=min_y, cell_size=safety_config.cell_size_meters, default_value=avg_value)

    @staticmethod
    def _sample_points(graph, source, target, edge_data) -> list[tuple[float, float]]:
        if "geometry" in edge_data:
            coords = list(edge_data["geometry"].coords)
            if len(coords) == 2:
                return coords
            sample = [coords[0], coords[len(coords) // 2], coords[-1]]
            return [(float(lon), float(lat)) for lon, lat in sample]

        source_node = graph.nodes[source]
        target_node = graph.nodes[target]
        mx = (float(source_node["x"]) + float(target_node["x"])) / 2
        my = (float(source_node["y"]) + float(target_node["y"])) / 2
        return [
            (float(source_node["x"]), float(source_node["y"])),
            (mx, my),
            (float(target_node["x"]), float(target_node["y"])),
        ]

    def _avg_metric(self, lookup: GridLookup, sample_points: list[tuple[float, float]]) -> float:
        values: list[float] = []
        for lon, lat in sample_points:
            x, y = self.to_projected.transform(lon, lat)
            values.append(lookup.value_at(x, y))
        return sum(values) / len(values) if values else lookup.default_value
