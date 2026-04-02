from __future__ import annotations

import csv
import io
import json
import math
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen

from pyproj import Transformer

from app.core.routing_profiles import routing_profiles_config
from app.core.safety_config import safety_config
from app.services.graph_service import GraphService


@dataclass
class LightingCell:
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    lamp_count: int = 0


class LightingService:
    def __init__(self) -> None:
        self.graph_service = GraphService()
        self.to_wgs84 = Transformer.from_crs(safety_config.projected_crs, safety_config.target_crs, always_xy=True)
        self.to_projected = Transformer.from_crs(safety_config.target_crs, safety_config.projected_crs, always_xy=True)
        self.data_dir = Path(__file__).resolve().parents[2] / "data" / "routing"
        self.raw_dir = Path(__file__).resolve().parents[2] / "data" / "lighting" / "raw"

    def build_lighting_grid(self) -> tuple[dict, dict]:
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

        cells: dict[tuple[int, int], LightingCell] = {}

        def get_cell(col: int, row: int) -> LightingCell:
            key = (col, row)
            if key not in cells:
                cell_min_x = min_x + col * cell_size
                cell_min_y = min_y + row * cell_size
                cells[key] = LightingCell(
                    min_x=cell_min_x,
                    min_y=cell_min_y,
                    max_x=cell_min_x + cell_size,
                    max_y=cell_min_y + cell_size,
                )
            return cells[key]

        rows_data = self._download_rows()
        out_of_bounds = 0
        for row in rows_data:
            x = self._parse_float(row.get("X_UTM"))
            y = self._parse_float(row.get("Y_UTM"))
            if x is None or y is None:
                continue
            col = int((x - min_x) // cell_size)
            row_index = int((y - min_y) // cell_size)
            if not (0 <= col < cols and 0 <= row_index < rows):
                out_of_bounds += 1
                continue
            get_cell(col, row_index).lamp_count += 1

        counts = [cell.lamp_count for cell in cells.values()]
        normalized_counts = self._normalize(counts)

        features: list[dict] = []
        deficits: list[float] = []
        for idx, (((col, row), cell), normalized_score) in enumerate(zip(cells.items(), normalized_counts)):
            deficit = 1.0 - normalized_score
            deficits.append(deficit)
            features.append(
                {
                    "type": "Feature",
                    "geometry": self._cell_polygon(cell),
                    "properties": {
                        "cellId": f"lighting-grid-{idx:06d}",
                        "col": col,
                        "row": row,
                        "lampCount": cell.lamp_count,
                        "lightingScore": round(normalized_score, 4),
                        "lightingDeficit": round(deficit, 4),
                    },
                }
            )

        collection = {"type": "FeatureCollection", "features": features}
        metadata = {
            "version": routing_profiles_config.cache_version,
            "cellSizeMeters": cell_size,
            "cellCount": len(features),
            "graphSource": graph_source,
            "recordsDownloaded": len(rows_data),
            "recordsUsed": sum(counts),
            "recordsOutOfBounds": out_of_bounds,
            "deficitAvg": round(sum(deficits) / len(deficits), 4) if deficits else 0,
            "source": routing_profiles_config.lighting_csv_url,
        }
        return collection, metadata

    def _download_rows(self) -> list[dict]:
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.raw_dir / "madrid_farolas.csv"

        request = Request(routing_profiles_config.lighting_csv_url, headers={"User-Agent": "Brisa/0.1 (slice-6 lighting)"})
        with urlopen(request, timeout=safety_config.download_timeout_seconds) as response:
            raw_bytes = response.read()

        output_path.write_bytes(raw_bytes)
        text = raw_bytes.decode("utf-8-sig", errors="ignore")
        delimiter = ";" if text[:1000].count(";") >= text[:1000].count(",") else ","
        return list(csv.DictReader(io.StringIO(text), delimiter=delimiter))

    @staticmethod
    def _normalize(values: list[float]) -> list[float]:
        if not values:
            return []
        min_v = min(values)
        max_v = max(values)
        if max_v == min_v:
            return [0.5 for _ in values]
        return [(value - min_v) / (max_v - min_v) for value in values]

    def _cell_polygon(self, cell: LightingCell) -> dict:
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
    def _parse_float(value: str | None) -> float | None:
        if value is None:
            return None
        cleaned = value.replace(".", "").replace(",", ".").strip()
        if cleaned.count(".") > 1:
            parts = cleaned.split(".")
            cleaned = "".join(parts[:-1]) + "." + parts[-1]
        try:
            return float(cleaned)
        except ValueError:
            return None
