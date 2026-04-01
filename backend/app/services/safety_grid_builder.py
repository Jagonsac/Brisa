from __future__ import annotations

import math
from dataclasses import dataclass

from pyproj import Transformer

from app.core.safety_config import safety_config
from app.services.accident_data_service import AccidentDataService
from app.services.graph_service import GraphService
from app.services.traffic_data_service import TrafficDataService


@dataclass
class CellAccumulator:
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    accident_count: int = 0
    weighted_accidents: float = 0.0
    traffic_exposure: float = 0.0
    hostile_length: float = 0.0
    bike_length: float = 0.0
    total_length: float = 0.0


class SafetyGridBuilder:
    def __init__(self) -> None:
        self.graph_service = GraphService()
        self.accident_service = AccidentDataService()
        self.traffic_service = TrafficDataService()
        self.to_projected = Transformer.from_crs(safety_config.target_crs, safety_config.projected_crs, always_xy=True)
        self.to_wgs84 = Transformer.from_crs(safety_config.projected_crs, safety_config.target_crs, always_xy=True)

    def build(self) -> tuple[dict, dict]:
        graph, graph_source = self.graph_service.get_graph()
        accidents, accidents_meta = self.accident_service.load_accidents()

        try:
            traffic_stations, traffic_meta = self.traffic_service.load_traffic_stations()
        except Exception as error:
            traffic_stations, traffic_meta = [], {"trafficFallbackUsed": True, "reason": str(error), "recordsUsed": 0}

        nodes = list(graph.nodes(data=True))
        projected_nodes = [self.to_projected.transform(float(data["x"]), float(data["y"])) for _, data in nodes]
        min_x = min(p[0] for p in projected_nodes)
        max_x = max(p[0] for p in projected_nodes)
        min_y = min(p[1] for p in projected_nodes)
        max_y = max(p[1] for p in projected_nodes)

        cell_size = safety_config.cell_size_meters
        cols = max(1, math.ceil((max_x - min_x) / cell_size))
        rows = max(1, math.ceil((max_y - min_y) / cell_size))

        cells: dict[tuple[int, int], CellAccumulator] = {}

        def get_cell(col: int, row: int) -> CellAccumulator:
            key = (col, row)
            if key not in cells:
                cell_min_x = min_x + col * cell_size
                cell_min_y = min_y + row * cell_size
                cells[key] = CellAccumulator(
                    min_x=cell_min_x,
                    min_y=cell_min_y,
                    max_x=cell_min_x + cell_size,
                    max_y=cell_min_y + cell_size,
                )
            return cells[key]

        for u, v, data in graph.edges(data=True):
            source = graph.nodes[u]
            target = graph.nodes[v]
            mx, my = self.to_projected.transform((float(source["x"]) + float(target["x"])) / 2, (float(source["y"]) + float(target["y"])) / 2)
            col = int((mx - min_x) // cell_size)
            row = int((my - min_y) // cell_size)
            if not (0 <= col < cols and 0 <= row < rows):
                continue

            cell = get_cell(col, row)
            length = float(data.get("length") or 0.0)
            highway = self._as_str(data.get("highway"))
            cycleway = self._as_str(data.get("cycleway"))

            cell.total_length += length

            if highway in safety_config.hostile_highway_classes:
                cell.hostile_length += length

            has_bike_feature = (
                highway == "cycleway"
                or bool(cycleway)
                or highway in safety_config.bike_friendly_highway_classes
                or self._as_str(data.get("bicycle")) in {"yes", "designated"}
            )
            if has_bike_feature:
                cell.bike_length += length

        for accident in accidents:
            col = int((accident.x - min_x) // cell_size)
            row = int((accident.y - min_y) // cell_size)
            if not (0 <= col < cols and 0 <= row < rows):
                continue
            cell = get_cell(col, row)
            cell.accident_count += accident.count
            cell.weighted_accidents += accident.weighted_score

        projected_stations = []
        for station in traffic_stations:
            px, py = self.to_projected.transform(station.lon, station.lat)
            projected_stations.append((px, py, station.intensity))

        if projected_stations:
            radius = float(safety_config.traffic_influence_radius_meters)
            for (col, row), cell in cells.items():
                cx = cell.min_x + cell_size / 2
                cy = cell.min_y + cell_size / 2
                exposure = 0.0
                for sx, sy, intensity in projected_stations:
                    distance = math.hypot(sx - cx, sy - cy)
                    if distance > radius:
                        continue
                    exposure += intensity / (1 + (distance / max(radius, 1))) ** 2
                cell.traffic_exposure = exposure

        weighted_acc_values = [cell.weighted_accidents for cell in cells.values()]
        traffic_values = [cell.traffic_exposure for cell in cells.values()]
        hostile_values = [cell.hostile_length / cell.total_length if cell.total_length else 0.0 for cell in cells.values()]
        bike_values = [cell.bike_length / cell.total_length if cell.total_length else 0.0 for cell in cells.values()]

        n_accidents = self._normalize_values(weighted_acc_values)
        n_traffic = self._normalize_values(traffic_values)
        n_hostile = self._normalize_values(hostile_values)
        n_bike = self._normalize_values(bike_values)

        weights = safety_config.weights
        raw_risks: list[float] = []
        normalized_components: list[tuple[float, float, float, float, float, float]] = []

        for idx, cell in enumerate(cells.values()):
            risk = (
                weights.accidents * n_accidents[idx]
                + weights.traffic * n_traffic[idx]
                + weights.hostile_roads * n_hostile[idx]
                - weights.bike_infra * n_bike[idx]
            )
            raw_risks.append(risk)
            normalized_components.append((n_accidents[idx], n_traffic[idx], n_hostile[idx], n_bike[idx], hostile_values[idx], bike_values[idx]))

        normalized_risks = self._normalize_values(raw_risks, lower_q=0, upper_q=100)

        features = []
        risk_scores = []
        safety_scores = []

        for index, (((col, row), cell), (_, _, _, _, hostile_ratio, bike_ratio), risk_norm) in enumerate(
            zip(cells.items(), normalized_components, normalized_risks)
        ):
            safety_score = max(0, min(100, int(round(100 * (1 - risk_norm)))))
            risk_score = max(0, min(100, int(round(risk_norm * 100))))
            risk_scores.append(risk_score)
            safety_scores.append(safety_score)

            polygon = self._cell_polygon(cell)
            explanation = self._build_explanation(
                safety_score=safety_score,
                accident_count=cell.accident_count,
                traffic=cell.traffic_exposure,
                hostile_ratio=hostile_ratio,
                bike_ratio=bike_ratio,
            )

            features.append(
                {
                    "type": "Feature",
                    "geometry": polygon,
                    "properties": {
                        "cellId": f"madrid-grid-{index:06d}",
                        "safetyScore": safety_score,
                        "riskScore": risk_score,
                        "accidentCount": cell.accident_count,
                        "weightedAccidentScore": round(cell.weighted_accidents, 3),
                        "trafficExposure": round(cell.traffic_exposure, 6),
                        "hostileRoadExposure": round(hostile_ratio, 4),
                        "bikeInfraScore": round(bike_ratio, 4),
                        "explanation": explanation,
                    },
                }
            )

        collection = {"type": "FeatureCollection", "features": features}
        metadata = {
            "version": safety_config.version,
            "cellSizeMeters": cell_size,
            "cellCount": len(features),
            "scoreMin": min(safety_scores) if safety_scores else 0,
            "scoreMax": max(safety_scores) if safety_scores else 0,
            "scoreAvg": round(sum(safety_scores) / len(safety_scores), 2) if safety_scores else 0,
            "weights": {
                "accidents": weights.accidents,
                "traffic": weights.traffic,
                "hostileRoads": weights.hostile_roads,
                "bikeInfra": weights.bike_infra,
            },
            "sources": {
                "bikeAccidents": bool(accidents_meta.get("recordsUsed", 0)),
                "traffic": bool(traffic_meta.get("recordsUsed", 0)),
                "osmBikeInfra": True,
            },
            "trafficFallbackUsed": bool(traffic_meta.get("trafficFallbackUsed", True)),
            "graphSource": graph_source,
            "accidents": accidents_meta,
            "traffic": traffic_meta,
        }
        return collection, metadata

    def _cell_polygon(self, cell: CellAccumulator) -> dict:
        corners = [
            (cell.min_x, cell.min_y),
            (cell.max_x, cell.min_y),
            (cell.max_x, cell.max_y),
            (cell.min_x, cell.max_y),
            (cell.min_x, cell.min_y),
        ]
        ring = []
        for x, y in corners:
            lon, lat = self.to_wgs84.transform(x, y)
            ring.append([round(lon, 7), round(lat, 7)])
        return {"type": "Polygon", "coordinates": [ring]}

    @staticmethod
    def _normalize_values(values: list[float], lower_q: int = 5, upper_q: int = 95) -> list[float]:
        if not values:
            return []
        sorted_values = sorted(values)
        low_idx = int((lower_q / 100) * (len(sorted_values) - 1))
        high_idx = int((upper_q / 100) * (len(sorted_values) - 1))
        low = sorted_values[low_idx]
        high = sorted_values[high_idx]
        if math.isclose(high, low):
            return [0.0 for _ in values]

        normalized = []
        for value in values:
            clipped = max(low, min(high, value))
            normalized.append((clipped - low) / (high - low))
        return normalized

    @staticmethod
    def _as_str(value) -> str:
        if isinstance(value, list):
            return str(value[0]) if value else ""
        if value is None:
            return ""
        return str(value)

    @staticmethod
    def _build_explanation(*, safety_score: int, accident_count: int, traffic: float, hostile_ratio: float, bike_ratio: float) -> list[str]:
        messages = []
        if accident_count >= 4:
            messages.append("Accidentalidad ciclista alta en esta celda")
        elif accident_count >= 1:
            messages.append("Accidentalidad ciclista moderada")
        else:
            messages.append("Sin accidentes ciclistas recientes detectados")

        if traffic > 0.5:
            messages.append("Exposición a tráfico motorizado elevada")
        elif traffic > 0.15:
            messages.append("Exposición a tráfico motorizado media")
        else:
            messages.append("Exposición a tráfico motorizado baja")

        if hostile_ratio > 0.45:
            messages.append("Predomina viario hostil de mayor jerarquía")
        elif bike_ratio > 0.35:
            messages.append("Buena presencia de infraestructura o vías bike-friendly")

        if safety_score >= 75:
            messages.append("Zona comparativamente más favorable para ciclismo")
        elif safety_score <= 35:
            messages.append("Zona comparativamente menos favorable para ciclismo")

        return messages[:3]
