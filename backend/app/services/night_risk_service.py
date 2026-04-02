from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import time

from pyproj import Transformer

from app.core.routing_profiles import routing_profiles_config
from app.core.safety_config import safety_config
from app.services.accident_data_service import AccidentDataService
from app.services.graph_service import GraphService


@dataclass
class NightRiskCell:
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    accident_count: int = 0
    weighted_accidents: float = 0.0


class NightRiskService:
    def __init__(self) -> None:
        self.graph_service = GraphService()
        self.accident_service = AccidentDataService()
        self.to_projected = Transformer.from_crs(safety_config.target_crs, safety_config.projected_crs, always_xy=True)
        self.to_wgs84 = Transformer.from_crs(safety_config.projected_crs, safety_config.target_crs, always_xy=True)

    def build_night_risk_grid(self) -> tuple[dict, dict]:
        graph, graph_source = self.graph_service.get_graph()
        nodes = list(graph.nodes(data=True))
        projected_nodes = [self.to_projected.transform(float(data["x"]), float(data["y"])) for _, data in nodes]

        min_x = min(p[0] for p in projected_nodes)
        max_x = max(p[0] for p in projected_nodes)
        min_y = min(p[1] for p in projected_nodes)
        max_y = max(p[1] for p in projected_nodes)

        cell_size = safety_config.cell_size_meters
        cols = max(1, math.ceil((max_x - min_x) / cell_size))
        rows = max(1, math.ceil((max_y - min_y) / cell_size))

        cells: dict[tuple[int, int], NightRiskCell] = {}

        def get_cell(col: int, row: int) -> NightRiskCell:
            key = (col, row)
            if key not in cells:
                cell_min_x = min_x + col * cell_size
                cell_min_y = min_y + row * cell_size
                cells[key] = NightRiskCell(cell_min_x, cell_min_y, cell_min_x + cell_size, cell_min_y + cell_size)
            return cells[key]

        rows_data = self.accident_service.load_raw_rows()
        used_rows = 0
        for row in rows_data:
            hour = self._parse_hour(row.get("hora"))
            if hour is None or not self._is_night_hour(hour):
                continue

            x = self.accident_service.parse_float(row.get("coordenada_x_utm"))
            y = self.accident_service.parse_float(row.get("coordenada_y_utm"))
            if x is None or y is None:
                continue

            lon, lat = self.accident_service.to_wgs84.transform(x, y)
            px, py = self.to_projected.transform(lon, lat)
            col = int((px - min_x) // cell_size)
            row_index = int((py - min_y) // cell_size)
            if not (0 <= col < cols and 0 <= row_index < rows):
                continue
            cell = get_cell(col, row_index)
            cell.accident_count += 1
            cell.weighted_accidents += self.accident_service.severity_weight(row)
            used_rows += 1

        values = [cell.weighted_accidents for cell in cells.values()]
        normalized_values = self._normalize(values)

        features = []
        for idx, (((col, row), cell), risk_norm) in enumerate(zip(cells.items(), normalized_values)):
            features.append(
                {
                    "type": "Feature",
                    "geometry": self._cell_polygon(cell),
                    "properties": {
                        "cellId": f"night-risk-grid-{idx:06d}",
                        "col": col,
                        "row": row,
                        "nightAccidentCount": cell.accident_count,
                        "nightWeightedAccidentScore": round(cell.weighted_accidents, 3),
                        "nightRisk": round(risk_norm, 4),
                    },
                }
            )

        return {
            "type": "FeatureCollection",
            "features": features,
        }, {
            "version": routing_profiles_config.cache_version,
            "cellSizeMeters": cell_size,
            "cellCount": len(features),
            "graphSource": graph_source,
            "recordsDownloaded": len(rows_data),
            "recordsUsed": used_rows,
            "nightStartHour": routing_profiles_config.night_start_hour,
            "nightEndHour": routing_profiles_config.night_end_hour,
        }

    def _is_night_hour(self, value: int) -> bool:
        start = routing_profiles_config.night_start_hour
        end = routing_profiles_config.night_end_hour
        if start < end:
            return start <= value < end
        return value >= start or value < end

    @staticmethod
    def _parse_hour(value: str | None) -> int | None:
        if not value:
            return None
        text = str(value).strip()
        if not text:
            return None
        hour_text = text.split(":")[0].strip()
        digits = "".join(ch for ch in hour_text if ch.isdigit())
        if not digits:
            return None
        hour = int(digits)
        if 0 <= hour <= 23:
            return hour
        return None

    @staticmethod
    def _normalize(values: list[float]) -> list[float]:
        if not values:
            return []
        min_v = min(values)
        max_v = max(values)
        if max_v == min_v:
            return [0.3 for _ in values]
        return [(value - min_v) / (max_v - min_v) for value in values]

    def _cell_polygon(self, cell: NightRiskCell) -> dict:
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
