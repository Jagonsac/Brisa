from __future__ import annotations

import csv
import io
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from pyproj import Transformer

from app.core.routing_profiles import routing_profiles_config
from app.core.safety_config import safety_config
from app.services.bike_legality_service import osm_bike_infra_score
from app.services.graph_service import GraphService


@dataclass
class SignalPoint:
    x: float
    y: float
    value: float


class PointIndex:
    def __init__(self, points: list[SignalPoint], cell_size: float = 120.0) -> None:
        self.cell_size = cell_size
        self.cells: dict[tuple[int, int], list[SignalPoint]] = {}
        for point in points:
            key = (int(point.x // cell_size), int(point.y // cell_size))
            self.cells.setdefault(key, []).append(point)

    def nearby_sum(self, x: float, y: float, radius: float) -> float:
        if not self.cells:
            return 0.0
        cell_radius = max(1, int(math.ceil(radius / self.cell_size)))
        cx = int(x // self.cell_size)
        cy = int(y // self.cell_size)
        r2 = radius * radius
        acc = 0.0
        for col in range(cx - cell_radius, cx + cell_radius + 1):
            for row in range(cy - cell_radius, cy + cell_radius + 1):
                for point in self.cells.get((col, row), []):
                    dx = point.x - x
                    dy = point.y - y
                    d2 = dx * dx + dy * dy
                    if d2 <= r2:
                        distance = max(1.0, math.sqrt(d2))
                        acc += point.value / (1.0 + distance / 20.0)
        return acc


class EdgeSafetyService:
    def __init__(self) -> None:
        self.graph_service = GraphService()
        self.cache_dir = Path(__file__).resolve().parents[2] / "data" / "routing"
        self.raw_dir = Path(__file__).resolve().parents[2] / "data"
        self.to_projected = Transformer.from_crs(safety_config.target_crs, safety_config.projected_crs, always_xy=True)
        self.to_wgs84 = Transformer.from_crs(safety_config.projected_crs, safety_config.target_crs, always_xy=True)

    def build_edge_metrics(self) -> dict:
        graph, graph_source = self.graph_service.get_graph()

        sources = self._load_sources()
        indexes = {key: PointIndex(value) for key, value in sources["points"].items()}

        metrics: dict[str, dict] = {}
        day_values = []
        night_values = []

        for u, v, key, data in graph.edges(keys=True, data=True):
            edge_id = f"{u}:{v}:{key}"
            length = float(data.get("length") or 1.0)
            samples = self._sample_points(graph, u, v, data)
            if not samples:
                continue

            lanes_value = self._parse_lanes(data.get("lanes"))
            maxspeed = self._parse_maxspeed(data.get("maxspeed"))
            highway_class = self._highway_class(data.get("highway"))
            bike_infra_osm = osm_bike_infra_score(data)

            traffic_exposure = self._signal_avg(indexes.get("traffic"), samples, safety_config.traffic_radius_m)
            imd_score = self._signal_avg(indexes.get("imd"), samples, safety_config.imd_radius_m)
            general_accidents = self._signal_avg(indexes.get("general_accidents"), samples, safety_config.accident_radius_m)
            bike_accidents = self._signal_avg(indexes.get("bike_accidents"), samples, safety_config.accident_radius_m)
            night_accidents = self._signal_avg(indexes.get("night_accidents"), samples, safety_config.accident_radius_m)
            lighting_density = self._signal_avg(indexes.get("lighting"), samples, safety_config.lighting_radius_m)
            bike_presence = self._signal_avg(indexes.get("bike_counts"), samples, safety_config.bike_presence_radius_m)
            crossings = self._signal_avg(indexes.get("crossings"), samples, safety_config.crossing_radius_m)
            bike_crossings = self._signal_avg(indexes.get("bike_crossings"), samples, safety_config.crossing_radius_m)

            road_hostility = self._road_hostility(highway_class=highway_class, lanes=lanes_value, maxspeed=maxspeed, bike_infra=bike_infra_osm)
            junction_complexity = self._junction_complexity(graph, u, v, crossings)

            accident_general_smoothed = self._smoothed_accident(general_accidents, exposure=(length / 100.0) + traffic_exposure + junction_complexity)
            bike_accident_smoothed = self._smoothed_accident(bike_accidents, exposure=(length / 120.0) + traffic_exposure * 0.6)
            night_accident_smoothed = self._smoothed_accident(night_accidents, exposure=(length / 140.0) + traffic_exposure)

            lighting_deficit = 1.0 - self._clamp01(lighting_density)
            bike_bonus = self._clamp01(bike_presence * 0.25 + bike_infra_osm * 0.65 + bike_crossings * 0.2)

            day_risk = self._clamp01(
                safety_config.day_weights["road_hostility"] * road_hostility
                + safety_config.day_weights["traffic"] * self._clamp01(0.6 * traffic_exposure + 0.4 * imd_score)
                + safety_config.day_weights["junction"] * self._clamp01(junction_complexity)
                + safety_config.day_weights["accident_general"] * self._clamp01(accident_general_smoothed)
                + safety_config.day_weights["accident_bike"] * self._clamp01(bike_accident_smoothed)
                - safety_config.day_weights["bike_bonus"] * bike_bonus
            )

            night_traffic_factor = self._clamp01(0.7 * imd_score + 0.3 * traffic_exposure)
            night_risk = self._clamp01(
                day_risk
                + safety_config.night_weights["lighting"] * lighting_deficit
                + safety_config.night_weights["night_accidents"] * self._clamp01(night_accident_smoothed)
                + safety_config.night_weights["night_traffic"] * night_traffic_factor
                + safety_config.night_weights["junction"] * self._clamp01(junction_complexity)
            )

            metrics[edge_id] = {
                "safetyRiskNormalized": round(day_risk, 6),
                "nightRiskNormalized": round(night_risk, 6),
                "lightingDeficitNormalized": round(lighting_deficit, 6),
                "motorTrafficExposureScore": round(self._clamp01(0.5 * traffic_exposure + 0.5 * imd_score), 6),
                "roadHostilityScore": round(self._clamp01(road_hostility), 6),
                "junctionComplexityScore": round(self._clamp01(junction_complexity), 6),
                "bikeInfrastructureScore": round(bike_bonus, 6),
                "generalAccidentScore": round(self._clamp01(accident_general_smoothed), 6),
                "bikeAccidentScore": round(self._clamp01(bike_accident_smoothed), 6),
                "nightAccidentScore": round(self._clamp01(night_accident_smoothed), 6),
                "nightTrafficFactor": round(night_traffic_factor, 6),
                "highwayClass": highway_class,
                "lanesValue": lanes_value,
                "maxspeedValue": maxspeed,
            }
            day_values.append(day_risk)
            night_values.append(night_risk)

        metadata = {
            "version": routing_profiles_config.cache_version,
            "updatedAt": datetime.now(timezone.utc).isoformat(),
            "graphSource": graph_source,
            "edgeCount": len(metrics),
            "riskStats": {
                "dayAvg": round(sum(day_values) / len(day_values), 4) if day_values else 0.0,
                "nightAvg": round(sum(night_values) / len(night_values), 4) if night_values else 0.0,
            },
            "datasets": sources["meta"],
        }

        return {"version": routing_profiles_config.cache_version, "edges": metrics, "metadata": metadata}

    def _load_sources(self) -> dict:
        points: dict[str, list[SignalPoint]] = {
            "general_accidents": self._load_accidents(safety_config.general_accidents_csv_url, bike_only=False, night_only=False),
            "bike_accidents": self._load_accidents(safety_config.bike_accidents_csv_url, bike_only=True, night_only=False),
            "night_accidents": self._load_accidents(safety_config.general_accidents_csv_url, bike_only=False, night_only=True),
            "traffic": self._load_point_csv(
                safety_config.traffic_non_permanent_csv_url,
                lat_candidates=("latitud", "latitude", "lat"),
                lon_candidates=("longitud", "longitude", "lon"),
                value_candidates=("total", "ligeros", "intensidad", "imd"),
                fallback=1.0,
            ),
            "imd": self._load_point_csv(
                safety_config.imd_csv_url,
                lat_candidates=("latitud", "latitude", "lat"),
                lon_candidates=("longitud", "longitude", "lon"),
                value_candidates=("intensidad", "imd", "valor", "total"),
                fallback=0.8,
            ),
            "lighting": self._load_utm_point_csv(
                safety_config.lighting_csv_url,
                x_candidates=("X_UTM", "utm_x", "x_utm"),
                y_candidates=("Y_UTM", "utm_y", "y_utm"),
                value=1.0,
            ),
            "bike_counts": self._load_point_csv(
                safety_config.bike_counts_csv_url,
                lat_candidates=("latitude", "latitud", "lat"),
                lon_candidates=("longitude", "longitud", "lon"),
                value_candidates=("bicicletas",),
                fallback=0.5,
            ),
            "crossings": self._load_point_csv(
                safety_config.crossings_csv_url,
                lat_candidates=("latitud", "latitude", "lat"),
                lon_candidates=("longitud", "longitude", "lon"),
                value_candidates=("id", "codigo"),
                fallback=0.8,
            ),
            "bike_crossings": self._load_point_csv(
                safety_config.bike_crossings_csv_url,
                lat_candidates=("latitud", "latitude", "lat"),
                lon_candidates=("longitud", "longitude", "lon"),
                value_candidates=("id", "codigo"),
                fallback=1.0,
            ),
        }
        meta = {name: {"records": len(values)} for name, values in points.items()}
        return {"points": points, "meta": meta}

    def _load_accidents(self, url: str, *, bike_only: bool, night_only: bool) -> list[SignalPoint]:
        rows = self._download_csv_rows(url)
        out: list[SignalPoint] = []
        for row in rows:
            x = self._parse_float(row.get("coordenada_x_utm"))
            y = self._parse_float(row.get("coordenada_y_utm"))
            if x is None or y is None:
                continue
            if bike_only and "bicic" not in str(row.get("tipo_vehiculo", "")).lower():
                continue
            if night_only:
                hour = self._parse_hour(row.get("hora"))
                if hour is None or not (hour >= routing_profiles_config.night_start_hour or hour < routing_profiles_config.night_end_hour):
                    continue

            severity = self._parse_severity(row.get("cod_lesividad"), row.get("lesividad"))
            out.append(SignalPoint(x=x, y=y, value=severity))
        return out

    def _load_point_csv(
        self,
        url: str,
        *,
        lat_candidates: tuple[str, ...],
        lon_candidates: tuple[str, ...],
        value_candidates: tuple[str, ...],
        fallback: float,
    ) -> list[SignalPoint]:
        rows = self._download_csv_rows(url)
        out: list[SignalPoint] = []
        for row in rows:
            lat = self._pick_float(row, lat_candidates)
            lon = self._pick_float(row, lon_candidates)
            if lat is None or lon is None:
                continue
            x, y = self.to_projected.transform(lon, lat)
            value = self._pick_float(row, value_candidates)
            out.append(SignalPoint(x=x, y=y, value=float(value if value is not None else fallback)))
        return out

    def _load_utm_point_csv(self, url: str, *, x_candidates: tuple[str, ...], y_candidates: tuple[str, ...], value: float) -> list[SignalPoint]:
        rows = self._download_csv_rows(url)
        out: list[SignalPoint] = []
        for row in rows:
            x = self._pick_float(row, x_candidates)
            y = self._pick_float(row, y_candidates)
            if x is None or y is None:
                continue
            out.append(SignalPoint(x=x, y=y, value=value))
        return out

    def _download_csv_rows(self, url: str) -> list[dict]:
        safe_name = url.split("/")[-1].split("?")[0] or "dataset.csv"
        output = self.raw_dir / "routing" / "raw" / safe_name
        output.parent.mkdir(parents=True, exist_ok=True)

        request = Request(url, headers={"User-Agent": "Brisa/0.1 routing-hardening"})
        try:
            with urlopen(request, timeout=safety_config.download_timeout_seconds) as response:
                raw = response.read()
            output.write_bytes(raw)
        except Exception:
            if output.exists():
                raw = output.read_bytes()
            else:
                return []

        text = raw.decode("utf-8-sig", errors="ignore")
        delimiter = ";" if text[:2000].count(";") >= text[:2000].count(",") else ","
        return list(csv.DictReader(io.StringIO(text), delimiter=delimiter))

    @staticmethod
    def _sample_points(graph, u, v, data) -> list[tuple[float, float]]:
        if "geometry" in data:
            coords = list(data["geometry"].coords)
            if len(coords) <= 3:
                return [(float(lon), float(lat)) for lon, lat in coords]
            picks = [coords[0], coords[len(coords) // 2], coords[-1]]
            return [(float(lon), float(lat)) for lon, lat in picks]

        a = graph.nodes[u]
        b = graph.nodes[v]
        mx = (float(a["x"]) + float(b["x"])) / 2
        my = (float(a["y"]) + float(b["y"])) / 2
        return [(float(a["x"]), float(a["y"])), (mx, my), (float(b["x"]), float(b["y"]))]

    def _signal_avg(self, index: PointIndex | None, samples: list[tuple[float, float]], radius: float) -> float:
        if index is None or not samples:
            return 0.0
        values = []
        for lon, lat in samples:
            x, y = self.to_projected.transform(lon, lat)
            values.append(index.nearby_sum(x, y, radius))
        if not values:
            return 0.0
        return self._clamp01(sum(values) / len(values) / safety_config.signal_scale_divisor)

    @staticmethod
    def _road_hostility(*, highway_class: str, lanes: float, maxspeed: float, bike_infra: float) -> float:
        base = safety_config.highway_hostility.get(highway_class, safety_config.highway_hostility["default"])
        lanes_penalty = min(1.0, lanes / 4.0) * 0.45
        speed_penalty = min(1.0, maxspeed / 50.0) * 0.4
        infra_relief = bike_infra * 0.55
        return max(0.0, min(1.0, base + lanes_penalty + speed_penalty - infra_relief))

    @staticmethod
    def _junction_complexity(graph, u, v, crossings_score: float) -> float:
        deg_u = min(8.0, float(graph.degree(u)))
        deg_v = min(8.0, float(graph.degree(v)))
        degree_signal = ((deg_u + deg_v) / 16.0)
        return max(0.0, min(1.0, 0.65 * degree_signal + 0.35 * crossings_score))

    @staticmethod
    def _smoothed_accident(observed: float, *, exposure: float) -> float:
        prior = safety_config.accident_prior_mean
        alpha = safety_config.accident_prior_strength
        return (observed + alpha * prior) / (max(exposure, 0.1) + alpha)

    @staticmethod
    def _parse_lanes(value) -> float:
        if value is None:
            return 1.0
        if isinstance(value, list):
            values = [EdgeSafetyService._parse_lanes(item) for item in value]
            return sum(values) / len(values)
        text = str(value).strip().lower()
        text = text.replace(";", "|").split("|")[0]
        digits = "".join(ch for ch in text if ch.isdigit() or ch == ".")
        if not digits:
            return 1.0
        try:
            return max(1.0, min(8.0, float(digits)))
        except ValueError:
            return 1.0

    @staticmethod
    def _parse_maxspeed(value) -> float:
        if value is None:
            return 30.0
        if isinstance(value, list):
            values = [EdgeSafetyService._parse_maxspeed(item) for item in value]
            return sum(values) / len(values)
        text = str(value).lower().strip()
        digits = "".join(ch for ch in text if ch.isdigit())
        if not digits:
            return 30.0
        speed = float(digits)
        if "mph" in text:
            speed *= 1.60934
        return max(10.0, min(120.0, speed))

    @staticmethod
    def _highway_class(value) -> str:
        if isinstance(value, list):
            value = value[0] if value else "unknown"
        return str(value or "unknown").lower()

    @staticmethod
    def _pick_float(row: dict, candidates: tuple[str, ...]) -> float | None:
        lowered = {str(key).lower(): value for key, value in row.items()}
        for candidate in candidates:
            value = lowered.get(candidate.lower())
            parsed = EdgeSafetyService._parse_float(value)
            if parsed is not None:
                return parsed
        return None

    @staticmethod
    def _parse_float(value) -> float | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip().replace(" ", "")
        if not text:
            return None
        if text.count(",") == 1 and text.count(".") >= 1:
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", ".")
        try:
            return float(text)
        except ValueError:
            return None

    @staticmethod
    def _parse_severity(code, label) -> float:
        parsed = EdgeSafetyService._parse_float(code)
        if parsed is not None:
            if parsed <= 3:
                return 1.0
            if parsed <= 7:
                return 0.7
            return 0.45
        text = str(label or "").lower()
        if "grave" in text or "falle" in text:
            return 1.0
        if "leve" in text:
            return 0.55
        return 0.6

    @staticmethod
    def _parse_hour(value) -> int | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        digits = "".join(ch for ch in text.split(":")[0] if ch.isdigit())
        if not digits:
            return None
        hour = int(digits)
        return hour if 0 <= hour <= 23 else None

    @staticmethod
    def _clamp01(value: float) -> float:
        return max(0.0, min(1.0, float(value)))
