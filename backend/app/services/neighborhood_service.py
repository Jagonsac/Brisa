from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen

from app.core.safety_config import safety_config


@dataclass
class NeighborhoodArea:
    neighborhood_id: str
    name: str
    district: str
    geometry: dict


class NeighborhoodService:
    def __init__(self) -> None:
        self.raw_dir = Path(__file__).resolve().parents[2] / "data" / "safety" / "raw"
        self.boundaries_path = self.raw_dir / safety_config.neighborhoods_cache_filename

    def load_boundaries(self) -> tuple[list[NeighborhoodArea], dict]:
        payload, source = self._load_geojson_payload()
        features = payload.get("features", [])
        neighborhoods: list[NeighborhoodArea] = []

        for index, feature in enumerate(features):
            geometry = feature.get("geometry")
            if not geometry or geometry.get("type") not in {"Polygon", "MultiPolygon"}:
                continue

            props = feature.get("properties", {})
            code = str(props.get("COD_BAR") or props.get("CodigoBarrio") or props.get("codigo_barrio") or "").strip()
            neighborhood_id = code or f"madrid-barrio-{index + 1:03d}"
            name = str(props.get("NOMBRE") or props.get("BARRIO_MAY") or props.get("BARRIO") or props.get("name") or neighborhood_id)
            district = str(props.get("NOMDIS") or props.get("DISTRITO") or props.get("district") or "")

            neighborhoods.append(
                NeighborhoodArea(
                    neighborhood_id=neighborhood_id,
                    name=name.strip(),
                    district=district.strip(),
                    geometry=geometry,
                )
            )

        metadata = {
            "source": source,
            "neighborhoodCount": len(neighborhoods),
            "url": safety_config.neighborhoods_geojson_url,
        }
        return neighborhoods, metadata

    def _load_geojson_payload(self) -> tuple[dict, str]:
        if self.boundaries_path.exists():
            return json.loads(self.boundaries_path.read_text(encoding="utf-8")), "cache"

        self.raw_dir.mkdir(parents=True, exist_ok=True)
        request = Request(safety_config.neighborhoods_geojson_url, headers={"User-Agent": "Brisa/0.1 (safety neighborhoods)"})
        with urlopen(request, timeout=safety_config.download_timeout_seconds) as response:
            raw_bytes = response.read()

        self.boundaries_path.write_bytes(raw_bytes)
        return json.loads(raw_bytes.decode("utf-8", errors="ignore")), "download"

    @staticmethod
    def contains(geometry: dict, lon: float, lat: float) -> bool:
        geometry_type = geometry.get("type")
        if geometry_type == "Polygon":
            return NeighborhoodService._point_in_polygon_geometry(geometry.get("coordinates", []), lon, lat)
        if geometry_type == "MultiPolygon":
            polygons = geometry.get("coordinates", [])
            return any(NeighborhoodService._point_in_polygon_geometry(coords, lon, lat) for coords in polygons)
        return False

    @staticmethod
    def _point_in_polygon_geometry(polygon_coords: list, lon: float, lat: float) -> bool:
        if not polygon_coords:
            return False

        outer_ring = polygon_coords[0]
        if not NeighborhoodService._point_in_ring(outer_ring, lon, lat):
            return False

        inner_rings = polygon_coords[1:]
        for ring in inner_rings:
            if NeighborhoodService._point_in_ring(ring, lon, lat):
                return False
        return True

    @staticmethod
    def _point_in_ring(ring: list, lon: float, lat: float) -> bool:
        if len(ring) < 4:
            return False

        inside = False
        previous = ring[-1]
        for current in ring:
            x1, y1 = float(previous[0]), float(previous[1])
            x2, y2 = float(current[0]), float(current[1])

            intersects = (y1 > lat) != (y2 > lat)
            if intersects:
                slope = (x2 - x1) / ((y2 - y1) or 1e-12)
                candidate_x = x1 + (lat - y1) * slope
                if candidate_x >= lon:
                    inside = not inside

            previous = current

        return inside
