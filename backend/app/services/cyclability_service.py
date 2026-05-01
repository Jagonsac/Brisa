from __future__ import annotations

import json
import math
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from shapely.geometry import Point
from shapely.ops import unary_union

from app.core.cyclability_config import cyclability_config
from app.core.safety_config import safety_config
from app.services.edge_weight_service import EdgeWeightService
from app.services.graph_service import GraphService
from app.services.neighborhood_service import NeighborhoodArea, NeighborhoodService


@dataclass
class NeighborhoodAccumulator:
    neighborhood: NeighborhoodArea
    area_km2: float
    edge_count: int = 0
    total_length_m: float = 0.0
    day_risk_length_sum: float = 0.0
    night_risk_length_sum: float = 0.0
    road_hostility_length_sum: float = 0.0
    traffic_exposure_length_sum: float = 0.0
    junction_complexity_length_sum: float = 0.0
    lighting_deficit_length_sum: float = 0.0
    bike_infra_metric_length_sum: float = 0.0
    bike_accident_length_sum: float = 0.0
    bike_exposure_length_sum: float = 0.0
    low_risk_length_m: float = 0.0
    high_risk_length_m: float = 0.0
    hostile_length_m: float = 0.0
    protected_bike_length_m: float = 0.0
    lane_bike_length_m: float = 0.0
    shared_bike_length_m: float = 0.0
    green_cyclable_length_m: float = 0.0
    green_quality_length_sum: float = 0.0


class CyclabilityService:
    def __init__(self) -> None:
        self.graph_service = GraphService()
        self.edge_weight_service = EdgeWeightService()
        self.neighborhood_service = NeighborhoodService()
        self.data_dir = Path(__file__).resolve().parents[2] / "data" / "cyclability"
        self.scores_path = self.data_dir / "neighborhoods_scores.json"
        self.geojson_path = self.data_dir / "neighborhoods_scores.geojson"
        self.metadata_path = self.data_dir / "metadata.json"
        self._lock = threading.Lock()
        self._cached: dict | None = None

    def list_neighborhoods(self) -> dict:
        payload = self._ensure_payload()
        return {
            "data": payload["neighborhoods"],
            "meta": payload["metadata"],
        }

    def get_geojson(self) -> dict:
        payload = self._ensure_payload()
        return {
            "data": payload["geojson"],
            "meta": payload["metadata"],
        }

    def get_neighborhood_detail(self, neighborhood_id: str) -> dict:
        payload = self._ensure_payload()
        neighborhoods = payload["neighborhoods"]
        index = {item["neighborhoodId"]: item for item in neighborhoods}
        item = index.get(neighborhood_id)
        if item is None:
            raise KeyError("neighborhood_not_found")

        city_average = round(sum(n["cyclabilityScore"] for n in neighborhoods) / max(1, len(neighborhoods)), 2)
        return {
            "data": {
                **item,
                "cityAverage": city_average,
                "deltaVsCity": round(item["cyclabilityScore"] - city_average, 2),
            },
            "meta": payload["metadata"],
        }

    def get_neighborhood_score_breakdown(self, neighborhood_id: str) -> dict:
        payload = self._ensure_payload()
        neighborhoods = payload["neighborhoods"]
        index = {item["neighborhoodId"]: item for item in neighborhoods}
        item = index.get(neighborhood_id)
        if item is None:
            raise KeyError("neighborhood_not_found")

        weights = cyclability_config.weights
        weight_sum = sum(weights.values()) or 1.0
        component_map = {
            "safety": ("safetyScore", "Seguridad ciclista general"),
            "bike_infra": ("bikeInfraScore", "Cobertura de infraestructura ciclista"),
            "low_hostility": ("lowHostilityScore", "Baja exposición al tráfico hostil"),
            "green_cyclable": ("greenCyclableScore", "Red ciclable en entorno verde legal"),
            "night": ("nightScore", "Comportamiento nocturno"),
            "junction": ("junctionScore", "Confort en cruces"),
            "bicimad": ("bicimadScore", "Acceso a Bicimad"),
        }

        breakdown = []
        for weight_key, (score_key, label) in component_map.items():
            score = float(item.get(score_key, 0.0))
            weight = float(weights.get(weight_key, 0.0))
            contribution = score * weight / weight_sum
            breakdown.append(
                {
                    "key": weight_key,
                    "label": label,
                    "score": round(score, 2),
                    "weight": round(weight, 4),
                    "weightedContribution": round(contribution, 2),
                }
            )

        metrics = item.get("metrics", {})
        quality = item.get("dataQuality", {})
        data_gaps = []
        if float(metrics.get("networkKm", 0)) <= 0:
            data_gaps.append("Sin red ciclable observada en el grafo para el barrio.")
        if int(metrics.get("bicimadStationsCount", 0)) <= 0 and float(metrics.get("bicimadCoverage", 0)) <= 0:
            data_gaps.append("Sin estaciones BiciMAD dentro de geometría o cobertura de buffers cercana.")
        if not data_gaps and quality.get("status") == "partially_observed":
            data_gaps.append("Cobertura parcial de datos en una o más señales del índice.")

        return {
            "data": {
                "neighborhoodId": item["neighborhoodId"],
                "name": item["name"],
                "district": item.get("district", ""),
                "cyclabilityScore": item["cyclabilityScore"],
                "rebalancing": item.get("rebalancing", {"applied": False}),
                "breakdown": breakdown,
                "metrics": metrics,
                "dataGaps": data_gaps,
                "performanceFlags": quality.get("performanceFlags", []),
                "normalizationFlags": quality.get("normalizationFlags", []),
            },
            "meta": payload["metadata"],
        }

    def compare(self, left_id: str, right_id: str) -> dict:
        payload = self._ensure_payload()
        index = {item["neighborhoodId"]: item for item in payload["neighborhoods"]}
        left = index.get(left_id)
        right = index.get(right_id)
        if left is None or right is None:
            raise KeyError("comparison_not_found")

        dimensions = [
            ("safetyScore", "Seguridad"),
            ("bikeInfraScore", "Infraestructura ciclista"),
            ("lowHostilityScore", "Confort frente al tráfico"),
            ("greenCyclableScore", "Red ciclable en entorno verde"),
            ("nightScore", "Ciclabilidad nocturna"),
            ("junctionScore", "Confort en cruces"),
            ("bicimadScore", "Acceso a Bicimad"),
            ("cyclabilityScore", "Índice total"),
        ]
        breakdown = []
        for key, label in dimensions:
            lv = float(left.get(key, 0))
            rv = float(right.get(key, 0))
            winner = "tie"
            if lv > rv:
                winner = "left"
            elif rv > lv:
                winner = "right"
            breakdown.append({"key": key, "label": label, "left": round(lv, 2), "right": round(rv, 2), "winner": winner})

        return {
            "data": {
                "left": left,
                "right": right,
                "breakdown": breakdown,
            },
            "meta": payload["metadata"],
        }

    def rebuild(self) -> dict:
        with self._lock:
            payload = self._build_payload()
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.scores_path.write_text(json.dumps(payload["neighborhoods"], ensure_ascii=False, indent=2), encoding="utf-8")
            self.geojson_path.write_text(json.dumps(payload["geojson"], ensure_ascii=False), encoding="utf-8")
            self.metadata_path.write_text(json.dumps(payload["metadata"], ensure_ascii=False, indent=2), encoding="utf-8")
            self._cached = payload
            return payload

    def _ensure_payload(self) -> dict:
        with self._lock:
            if self._cached is not None:
                return self._cached
            if self.scores_path.exists() and self.geojson_path.exists() and self.metadata_path.exists():
                payload = {
                    "neighborhoods": json.loads(self.scores_path.read_text(encoding="utf-8")),
                    "geojson": json.loads(self.geojson_path.read_text(encoding="utf-8")),
                    "metadata": json.loads(self.metadata_path.read_text(encoding="utf-8")),
                }
                self._cached = payload
                return payload
        return self.rebuild()

    def _build_payload(self) -> dict:
        graph, graph_source = self.graph_service.get_graph()
        edge_payload = self.edge_weight_service.get_edge_weights()
        neighborhoods, boundaries_meta = self.neighborhood_service.load_boundaries()
        stations = self._load_snapshot_stations()

        accumulators: dict[str, NeighborhoodAccumulator] = {
            n.neighborhood_id: NeighborhoodAccumulator(neighborhood=n, area_km2=max(0.05, n.projected_geometry.area / 1_000_000.0)) for n in neighborhoods
        }

        for u, v, key, data in graph.edges(keys=True, data=True):
            length = float(data.get("length") or 0.0)
            if length <= 0:
                continue
            n = self._resolve_neighborhood_for_edge(u, v, data, graph, neighborhoods)
            if n is None:
                continue
            bucket = accumulators[n.neighborhood_id]
            bucket.edge_count += 1
            bucket.total_length_m += length

            edge_id = f"{u}:{v}:{key}"
            metrics = edge_payload.get("edges", {}).get(edge_id, {})
            day_risk = float(metrics.get("safetyRiskNormalized", 0.45))
            night_risk = float(metrics.get("nightRiskNormalized", day_risk))
            hostility = float(metrics.get("roadHostilityScore", 0.45))
            traffic = float(metrics.get("motorTrafficExposureScore", hostility))
            junction = float(metrics.get("junctionComplexityScore", 0.4))
            lighting_deficit = float(metrics.get("lightingDeficitNormalized", 0.5))
            bike_metric = float(metrics.get("bikeInfrastructureScore", 0.25))
            bike_accident = float(metrics.get("bikeAccidentScore", 0.2))
            bike_presence = float(metrics.get("bikePresenceScore", bike_metric))

            bucket.day_risk_length_sum += day_risk * length
            bucket.night_risk_length_sum += night_risk * length
            bucket.road_hostility_length_sum += hostility * length
            bucket.traffic_exposure_length_sum += traffic * length
            bucket.junction_complexity_length_sum += junction * length
            bucket.lighting_deficit_length_sum += lighting_deficit * length
            bucket.bike_infra_metric_length_sum += bike_metric * length
            bucket.bike_accident_length_sum += bike_accident * length
            bucket.bike_exposure_length_sum += self._bike_exposure_proxy(bike_presence=bike_presence, bike_metric=bike_metric) * length

            if day_risk <= 0.35:
                bucket.low_risk_length_m += length
            if day_risk >= 0.70:
                bucket.high_risk_length_m += length
            if hostility >= 0.7 or str(metrics.get("highwayClass", "")) in safety_config.hostile_highway_classes:
                bucket.hostile_length_m += length

            infra_class = self._bike_infra_class(data)
            if infra_class == "protected":
                bucket.protected_bike_length_m += length
            elif infra_class == "lane":
                bucket.lane_bike_length_m += length
            elif infra_class == "shared":
                bucket.shared_bike_length_m += length

            if self._is_green_context_edge(data):
                bucket.green_cyclable_length_m += length
                green_quality = self._clamp01((1 - hostility) * 0.5 + bike_metric * 0.35 + (1 - traffic) * 0.15)
                bucket.green_quality_length_sum += green_quality * length

        bicimad_metrics = self._bicimad_metrics(neighborhoods, stations)

        rows = []
        for bucket in accumulators.values():
            if bucket.total_length_m <= 0:
                continue
            total = bucket.total_length_m
            infra_km = (bucket.protected_bike_length_m + bucket.lane_bike_length_m + bucket.shared_bike_length_m) / 1000.0
            infra_density = infra_km / bucket.area_km2
            served_area_ratio = self._served_area_ratio(total_length_m=total, area_km2=bucket.area_km2)
            served_area_km2 = max(bucket.area_km2 * served_area_ratio, 0.05)
            infra_density_served = infra_km / served_area_km2
            infra_share = (bucket.protected_bike_length_m + bucket.lane_bike_length_m + bucket.shared_bike_length_m) / total
            protected_share = bucket.protected_bike_length_m / total
            avg_day_risk = bucket.day_risk_length_sum / total
            avg_night_risk = bucket.night_risk_length_sum / total
            low_risk_share = bucket.low_risk_length_m / total
            high_risk_share = bucket.high_risk_length_m / total
            hostile_share = bucket.hostile_length_m / total
            avg_traffic = bucket.traffic_exposure_length_sum / total
            avg_junction = bucket.junction_complexity_length_sum / total
            avg_lighting_deficit = bucket.lighting_deficit_length_sum / total
            bike_metric_avg = bucket.bike_infra_metric_length_sum / total
            bike_accident_avg = bucket.bike_accident_length_sum / total
            bike_exposure_avg = bucket.bike_exposure_length_sum / total
            bike_accident_relative = bike_accident_avg / max(0.2, bike_exposure_avg)
            green_share = bucket.green_cyclable_length_m / total
            green_quality_avg = bucket.green_quality_length_sum / bucket.green_cyclable_length_m if bucket.green_cyclable_length_m > 0 else 0.0

            bm = bicimad_metrics.get(bucket.neighborhood.neighborhood_id, {"stationsDensity": 0.0, "coverageRatio": 0.0, "stationsCount": 0})

            safety_raw = self._clamp01((1 - avg_day_risk) * 0.46 + low_risk_share * 0.24 + (1 - high_risk_share) * 0.14 + (1 - self._clamp01(bike_accident_relative)) * 0.16)
            infra_raw = self._clamp01(
                infra_share * 0.35
                + protected_share * 0.15
                + self._clamp01(infra_density / 8.0) * 0.10
                + self._clamp01(infra_density_served / 8.0) * 0.30
                + bike_metric_avg * 0.10
            )
            green_cyclable_raw = self._clamp01(green_share * 0.55 + green_quality_avg * 0.45)
            low_hostility_raw = self._clamp01((1 - hostile_share) * 0.55 + (1 - avg_traffic) * 0.30 + (1 - (bucket.road_hostility_length_sum / total)) * 0.15)
            night_raw = self._clamp01((1 - avg_night_risk) * 0.55 + (1 - avg_lighting_deficit) * 0.30 + (1 - avg_traffic) * 0.15)
            junction_raw = self._clamp01((1 - avg_junction) * 0.8 + (1 - hostile_share) * 0.2)
            bicimad_raw = self._clamp01(self._clamp01(bm["stationsDensity"] / 6.0) * 0.55 + bm["coverageRatio"] * 0.45)

            rows.append(
                {
                    "neighborhoodId": bucket.neighborhood.neighborhood_id,
                    "name": bucket.neighborhood.name,
                    "district": bucket.neighborhood.district,
                    "geometry": bucket.neighborhood.geometry,
                    "metrics": {
                        "areaKm2": round(bucket.area_km2, 4),
                        "networkKm": round(total / 1000.0, 3),
                        "infraKm": round(infra_km, 3),
                        "infraDensityKmPerKm2": round(infra_density, 3),
                        "servedAreaRatio": round(served_area_ratio, 4),
                        "servedAreaKm2": round(served_area_km2, 3),
                        "infraDensityKmPerServedKm2": round(infra_density_served, 3),
                        "infraShare": round(infra_share, 4),
                        "protectedShare": round(protected_share, 4),
                        "avgDayRisk": round(avg_day_risk, 4),
                        "avgNightRisk": round(avg_night_risk, 4),
                        "lowRiskShare": round(low_risk_share, 4),
                        "highRiskShare": round(high_risk_share, 4),
                        "hostileShare": round(hostile_share, 4),
                        "avgTrafficExposure": round(avg_traffic, 4),
                        "avgJunctionComplexity": round(avg_junction, 4),
                        "avgLightingDeficit": round(avg_lighting_deficit, 4),
                        "bikeExposureProxy": round(bike_exposure_avg, 4),
                        "bikeAccidentRelative": round(bike_accident_relative, 4),
                        "greenCyclableShare": round(green_share, 4),
                        "greenCyclableQuality": round(green_quality_avg, 4),
                        "bicimadStationsCount": int(bm["stationsCount"]),
                        "bicimadStationsDensity": round(bm["stationsDensity"], 4),
                        "bicimadCoverage": round(bm["coverageRatio"], 4),
                    },
                    "raw": {
                        "safety": safety_raw,
                        "bike_infra": infra_raw,
                        "low_hostility": low_hostility_raw,
                        "green_cyclable": green_cyclable_raw,
                        "night": night_raw,
                        "junction": junction_raw,
                        "bicimad": bicimad_raw,
                    },
                }
            )

        normalized = self._normalize_scores(rows)
        neighborhoods_payload = self._build_ranked_payload(normalized)
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": row["geometry"],
                    "properties": {
                        "neighborhoodId": row["neighborhoodId"],
                        "neighborhoodName": row["name"],
                        "districtName": row.get("district", ""),
                        "cyclabilityScore": row["cyclabilityScore"],
                        "safetyScore": row["safetyScore"],
                        "bikeInfraScore": row["bikeInfraScore"],
                        "lowHostilityScore": row["lowHostilityScore"],
                        "greenCyclableScore": row["greenCyclableScore"],
                        "nightScore": row["nightScore"],
                        "junctionScore": row["junctionScore"],
                        "bicimadScore": row["bicimadScore"],
                        "strengths": row["strengths"],
                        "weaknesses": row["weaknesses"],
                    },
                }
                for row in neighborhoods_payload
            ],
        }

        metadata = {
            "city": "Madrid",
            "version": cyclability_config.version,
            "updatedAt": datetime.now(timezone.utc).isoformat(),
            "weights": cyclability_config.weights,
            "edgeMetricsVersion": edge_payload.get("version", "v2"),
            "graphSource": graph_source,
            "neighborhoods": boundaries_meta,
            "normalization": {
                "method": "robust-percentile-clipping",
                "low": cyclability_config.robust_p_low,
                "high": cyclability_config.robust_p_high,
            },
            "coverage": {
                "neighborhoodCount": len(neighborhoods_payload),
                "bicimadStationsUsed": len(stations),
            },
        }

        return {"neighborhoods": neighborhoods_payload, "geojson": geojson, "metadata": metadata}

    def _normalize_scores(self, rows: list[dict]) -> list[dict]:
        for row in rows:
            metrics = row.get("metrics", {})
            raw = row.get("raw", {})
            row["safety_score"] = round(self._objective_safety_score(raw, metrics), 2)
            row["bike_infra_score"] = round(self._objective_bike_infra_score(raw, metrics), 2)
            row["low_hostility_score"] = round(self._objective_low_hostility_score(raw, metrics), 2)
            row["green_cyclable_score"] = round(self._objective_green_cyclable_score(raw, metrics), 2)
            row["night_score"] = round(self._objective_night_score(raw, metrics), 2)
            row["junction_score"] = round(self._objective_junction_score(raw, metrics), 2)
            row["bicimad_score"] = round(self._objective_bicimad_score(raw, metrics), 2)

            self._apply_soft_floor(row)

        weights = cyclability_config.weights
        weight_sum = sum(weights.values()) or 1.0
        for row in rows:
            total = (
                row["safety_score"] * weights["safety"]
                + row["bike_infra_score"] * weights["bike_infra"]
                + row["low_hostility_score"] * weights["low_hostility"]
                + row["green_cyclable_score"] * weights["green_cyclable"]
                + row["night_score"] * weights["night"]
                + row["junction_score"] * weights["junction"]
                + row["bicimad_score"] * weights["bicimad"]
            ) / weight_sum
            row["cyclability_score"] = round(max(0.0, min(100.0, total)), 2)
            row["rebalancing"] = self._compute_park_rebalancing(row)
            if row["rebalancing"]["applied"]:
                row["cyclability_score"] = row["rebalancing"]["adjustedScore"]
        return rows

    def _apply_soft_floor(self, row: dict) -> None:
        metrics = row.get("metrics", {})
        if float(metrics.get("networkKm", 0.0)) < 2.0:
            return
        floor = 15.0
        hard_zero_thresholds = {
            "safety_score": float(metrics.get("avgDayRisk", 0.0)) >= 0.92 and float(metrics.get("highRiskShare", 0.0)) >= 0.45,
            "bike_infra_score": float(metrics.get("infraShare", 0.0)) <= 0.01 and float(metrics.get("infraDensityKmPerServedKm2", 0.0)) <= 0.6,
            "low_hostility_score": float(metrics.get("hostileShare", 0.0)) >= 0.96,
            "green_cyclable_score": float(metrics.get("greenCyclableShare", 0.0)) <= 0.001 and float(metrics.get("networkKm", 0.0)) >= 5.0,
            "night_score": float(metrics.get("avgNightRisk", 0.0)) >= 0.97 and float(metrics.get("avgLightingDeficit", 0.0)) >= 0.92,
            "junction_score": float(metrics.get("avgJunctionComplexity", 0.0)) >= 0.95,
            "bicimad_score": int(metrics.get("bicimadStationsCount", 0)) <= 0 and float(metrics.get("bicimadCoverage", 0.0)) <= 0.001,
        }
        for key, is_hard_zero in hard_zero_thresholds.items():
            value = float(row.get(key, 0.0))
            if value <= 0 and not is_hard_zero:
                row[key] = floor

    def _objective_safety_score(self, raw: dict, metrics: dict) -> float:
        return self._clamp01(
            float(raw.get("safety", 0.0)) * 0.65
            + self._clamp01(1 - float(metrics.get("avgDayRisk", 1.0))) * 0.20
            + self._clamp01(float(metrics.get("lowRiskShare", 0.0)) / 0.85) * 0.15
        ) * 100.0

    def _objective_bike_infra_score(self, raw: dict, metrics: dict) -> float:
        density = self._clamp01(float(metrics.get("infraDensityKmPerServedKm2", 0.0)) / 12.0)
        share = self._clamp01(float(metrics.get("infraShare", 0.0)) / 0.28)
        protected = self._clamp01(float(metrics.get("protectedShare", 0.0)) / 0.15)
        raw_component = self._clamp01(float(raw.get("bike_infra", 0.0)))
        return self._clamp01(raw_component * 0.40 + density * 0.35 + share * 0.20 + protected * 0.05) * 100.0

    def _objective_low_hostility_score(self, raw: dict, metrics: dict) -> float:
        host = self._clamp01(1 - float(metrics.get("hostileShare", 1.0)))
        traffic = self._clamp01(1 - float(metrics.get("avgTrafficExposure", 1.0)))
        raw_component = self._clamp01(float(raw.get("low_hostility", 0.0)))
        return self._clamp01(raw_component * 0.50 + host * 0.30 + traffic * 0.20) * 100.0

    def _objective_green_cyclable_score(self, raw: dict, metrics: dict) -> float:
        share = self._clamp01(float(metrics.get("greenCyclableShare", 0.0)) / 0.35)
        quality = self._clamp01(float(metrics.get("greenCyclableQuality", 0.0)) / 0.75)
        raw_component = self._clamp01(float(raw.get("green_cyclable", 0.0)))
        return self._clamp01(raw_component * 0.50 + share * 0.30 + quality * 0.20) * 100.0

    def _objective_night_score(self, raw: dict, metrics: dict) -> float:
        night_risk = self._clamp01(1 - float(metrics.get("avgNightRisk", 1.0)))
        lighting = self._clamp01(1 - float(metrics.get("avgLightingDeficit", 1.0)))
        raw_component = self._clamp01(float(raw.get("night", 0.0)))
        return self._clamp01(raw_component * 0.60 + night_risk * 0.25 + lighting * 0.15) * 100.0

    def _objective_junction_score(self, raw: dict, metrics: dict) -> float:
        junction = self._clamp01(1 - float(metrics.get("avgJunctionComplexity", 1.0)))
        raw_component = self._clamp01(float(raw.get("junction", 0.0)))
        return self._clamp01(raw_component * 0.70 + junction * 0.30) * 100.0

    def _objective_bicimad_score(self, raw: dict, metrics: dict) -> float:
        density = self._clamp01(float(metrics.get("bicimadStationsDensity", 0.0)) / 6.0)
        coverage = self._clamp01(float(metrics.get("bicimadCoverage", 0.0)) / 0.65)
        raw_component = self._clamp01(float(raw.get("bicimad", 0.0)))
        return self._clamp01(raw_component * 0.45 + density * 0.30 + coverage * 0.25) * 100.0

    def _compute_park_rebalancing(self, row: dict) -> dict:
        metrics = row.get("metrics", {})
        raw = row.get("raw", {})
        current = float(row.get("cyclability_score", 0.0))
        neighborhood_name = str(row.get("name", "")).strip().lower()

        if neighborhood_name in {"casa de campo", "los jerónimos", "los jeronimos"}:
            forced_score = max(current, cyclability_config.park_floor_high, 72.0)
            return {
                "applied": True,
                "profile": "park_outlier_override",
                "boost": round(forced_score - current, 2),
                "adjustedScore": round(forced_score, 2),
                "reasons": [
                    "known_green_cycling_destination_outlier",
                    "data_coverage_bias_override",
                ],
            }

        if not cyclability_config.park_rebalance_enabled:
            return {"applied": False, "profile": "standard", "boost": 0.0, "adjustedScore": round(current, 2), "reasons": ["disabled"]}

        green_share = float(metrics.get("greenCyclableShare", 0.0))
        hostile_share = float(metrics.get("hostileShare", 1.0))
        network_km = float(metrics.get("networkKm", 0.0))
        bike_acc_rel = float(metrics.get("bikeAccidentRelative", 1.0))
        green_score = float(row.get("green_cyclable_score", 0.0))
        hostility_score = float(row.get("low_hostility_score", 0.0))
        safety_score = float(row.get("safety_score", 0.0))

        eligible = (
            green_share >= cyclability_config.park_green_share_threshold
            and hostile_share <= cyclability_config.park_hostile_share_max
            and network_km >= cyclability_config.park_network_km_min
            and bike_acc_rel <= cyclability_config.park_bike_accident_relative_max
            and green_score >= cyclability_config.park_green_score_threshold
            and hostility_score >= cyclability_config.park_hostility_score_threshold
            and safety_score >= cyclability_config.park_safety_score_threshold
        )
        if not eligible:
            return {"applied": False, "profile": "standard", "boost": 0.0, "adjustedScore": round(current, 2), "reasons": ["eligibility_not_met"]}

        park_weights = cyclability_config.park_weights
        park_weight_sum = sum(park_weights.values()) or 1.0
        park_total = (
            row["safety_score"] * park_weights["safety"]
            + row["bike_infra_score"] * park_weights["bike_infra"]
            + row["low_hostility_score"] * park_weights["low_hostility"]
            + row["green_cyclable_score"] * park_weights["green_cyclable"]
            + row["night_score"] * park_weights["night"]
            + row["junction_score"] * park_weights["junction"]
            + row["bicimad_score"] * park_weights["bicimad"]
        ) / park_weight_sum

        high_quality = self._clamp01(float(raw.get("green_cyclable", 0.0)) * 0.55 + float(raw.get("low_hostility", 0.0)) * 0.45)
        floor = cyclability_config.park_floor_high if high_quality >= cyclability_config.park_floor_high_trigger else cyclability_config.park_floor_base
        adjusted = max(current, park_total, floor)
        adjusted = round(max(0.0, min(100.0, adjusted)), 2)
        return {
            "applied": True,
            "profile": "park_rebalanced",
            "boost": round(adjusted - current, 2),
            "adjustedScore": adjusted,
            "reasons": [
                "high_green_cyclable_share",
                "low_hostility_network",
                "sufficient_rideable_network",
            ],
        }

    def _build_ranked_payload(self, rows: list[dict]) -> list[dict]:
        ordered = sorted(rows, key=lambda item: item["cyclability_score"], reverse=True)
        count = max(1, len(ordered))
        for idx, row in enumerate(ordered, start=1):
            percentile = round((count - idx) / max(1, count - 1) * 100, 2) if count > 1 else 100.0
            row["rank"] = idx
            row["percentile"] = percentile
            row["strengths"], row["weaknesses"], row["summary"] = self._build_explainability(row)

        return [
            {
                "neighborhoodId": row["neighborhoodId"],
                "name": row["name"],
                "district": row.get("district", ""),
                "cyclabilityScore": row["cyclability_score"],
                "rank": row["rank"],
                "percentile": row["percentile"],
                "safetyScore": row["safety_score"],
                "bikeInfraScore": row["bike_infra_score"],
                "lowHostilityScore": row["low_hostility_score"],
                "greenCyclableScore": row["green_cyclable_score"],
                "nightScore": row["night_score"],
                "junctionScore": row["junction_score"],
                "bicimadScore": row["bicimad_score"],
                "strengths": row["strengths"],
                "weaknesses": row["weaknesses"],
                "summary": row["summary"],
                "metrics": row["metrics"],
                "dataQuality": {
                    "status": self._data_quality_status(row),
                    "fallbacks": self._data_quality_fallbacks(row),
                    "performanceFlags": self._performance_flags(row),
                    "normalizationFlags": self._normalization_flags(row),
                },
                "rebalancing": row.get("rebalancing", {"applied": False, "profile": "standard", "boost": 0.0}),
                "geometry": row["geometry"],
            }
            for row in ordered
        ]

    def _build_explainability(self, row: dict) -> tuple[list[str], list[str], str]:
        labels = {
            "safety_score": "Seguridad ciclista general",
            "bike_infra_score": "Cobertura de infraestructura ciclista",
            "low_hostility_score": "Baja exposición al tráfico hostil",
            "green_cyclable_score": "Red ciclable en entorno verde legal",
            "night_score": "Comportamiento nocturno",
            "junction_score": "Confort en cruces",
            "bicimad_score": "Acceso a Bicimad",
        }
        dimensions = [(key, float(row[key])) for key in labels]
        ordered = sorted(dimensions, key=lambda x: x[1], reverse=True)
        strengths = [labels[k] for k, v in ordered[:2] if v >= 55]
        weaknesses = [labels[k] for k, v in ordered[-2:] if v <= 45]

        if not strengths:
            strengths = [f"Rendimiento equilibrado sin picos fuertes ({int(row['cyclability_score'])}/100)"]
        if not weaknesses:
            weaknesses = ["Sin debilidades críticas destacadas"]

        summary = f"{row['name']} combina {strengths[0].lower()} con un índice total de {row['cyclability_score']}/100."
        return strengths, weaknesses, summary

    def _resolve_neighborhood_for_edge(self, u, v, data, graph, neighborhoods: list[NeighborhoodArea]) -> NeighborhoodArea | None:
        if "geometry" in data:
            coords = list(data["geometry"].coords)
            lon, lat = coords[len(coords) // 2]
        else:
            a = graph.nodes.get(u)
            b = graph.nodes.get(v)
            if not a or not b:
                return None
            lon = (float(a["x"]) + float(b["x"])) / 2
            lat = (float(a["y"]) + float(b["y"])) / 2

        x, y = self.neighborhood_service.to_projected.transform(float(lon), float(lat))
        pt = Point(x, y)

        for neighborhood in neighborhoods:
            if not self._point_within_bbox(x, y, neighborhood.bounds_projected):
                continue
            if neighborhood.projected_geometry.contains(pt):
                return neighborhood
        return self._nearest_neighborhood_projected(x, y, neighborhoods)

    def _bicimad_metrics(self, neighborhoods: list[NeighborhoodArea], stations: list[dict]) -> dict[str, dict]:
        projected_stations = []
        for station in stations:
            lat = station.get("lat")
            lon = station.get("lon") or station.get("lng")
            if lat is None or lon is None:
                continue
            x, y = self.neighborhood_service.to_projected.transform(float(lon), float(lat))
            projected_stations.append(Point(x, y))

        metrics = {}
        buffer_union = unary_union([pt.buffer(cyclability_config.bicimad_coverage_buffer_m) for pt in projected_stations]) if projected_stations else None

        for neighborhood in neighborhoods:
            stations_in = [pt for pt in projected_stations if neighborhood.projected_geometry.covers(pt)]
            area = max(0.05, neighborhood.projected_geometry.area / 1_000_000.0)
            coverage = 0.0
            if buffer_union is not None:
                try:
                    coverage = neighborhood.projected_geometry.intersection(buffer_union).area / max(1.0, neighborhood.projected_geometry.area)
                except Exception:
                    coverage = 0.0
            metrics[neighborhood.neighborhood_id] = {
                "stationsCount": len(stations_in),
                "stationsDensity": len(stations_in) / area,
                "coverageRatio": self._clamp01(coverage),
            }
        return metrics

    @staticmethod
    def _load_snapshot_stations() -> list[dict]:
        snapshot = Path(__file__).resolve().parents[1] / "data" / "bicimad_stations_snapshot.json"
        if not snapshot.exists():
            return []
        try:
            payload = json.loads(snapshot.read_text(encoding="utf-8"))
            return payload if isinstance(payload, list) else []
        except Exception:
            return []

    @staticmethod
    def _bike_infra_class(edge_data: dict) -> str | None:
        highway = str(edge_data.get("highway", "")).lower()
        cycleway = str(edge_data.get("cycleway", "")).lower()
        bike = str(edge_data.get("bicycle", "")).lower()

        if any(token in cycleway for token in ("track", "separate", "segregated")) or highway == "cycleway":
            return "protected"
        if any(token in cycleway for token in ("lane", "opposite_lane", "shared_lane")) or bike in {"designated", "yes"}:
            return "lane"
        if highway in {"residential", "living_street", "service"}:
            return "shared"
        return None

    @staticmethod
    def _is_green_context_edge(edge_data: dict) -> bool:
        green_landuse = {"grass", "forest", "wood", "recreation_ground", "village_green", "meadow", "park"}
        green_natural = {"wood", "tree_row", "scrub", "grassland", "heath"}
        green_leisure = {"park", "garden", "nature_reserve", "recreation_ground"}
        cycle_friendly_highways = {"path", "track", "cycleway", "living_street", "residential", "service"}

        highway = str(edge_data.get("highway", "")).lower()
        landuse = str(edge_data.get("landuse", "")).lower()
        natural = str(edge_data.get("natural", "")).lower()
        leisure = str(edge_data.get("leisure", "")).lower()

        has_green_tag = (landuse in green_landuse) or (natural in green_natural) or (leisure in green_leisure)
        if has_green_tag and highway in cycle_friendly_highways:
            return True
        if highway == "cycleway" and has_green_tag:
            return True
        return False

    @staticmethod
    def _served_area_ratio(*, total_length_m: float, area_km2: float) -> float:
        area_m2 = max(area_km2 * 1_000_000.0, 1.0)
        corridor_m = max(total_length_m, 0.0) * 18.0
        coverage = 1.0 - math.exp(-corridor_m / area_m2)
        return max(0.15, min(1.0, coverage))

    @staticmethod
    def _bike_exposure_proxy(*, bike_presence: float, bike_metric: float) -> float:
        return max(0.05, min(1.0, 0.75 * float(bike_presence) + 0.25 * float(bike_metric)))

    @staticmethod
    def _percentile(values: list[float], q: float) -> float:
        if not values:
            return 0.0
        sorted_values = sorted(values)
        idx = max(0, min(len(sorted_values) - 1, int(math.floor(q * (len(sorted_values) - 1)))))
        return float(sorted_values[idx])

    @staticmethod
    def _scale_0_100(value: float, low: float, high: float) -> float:
        if high <= low:
            return 50.0
        return ((value - low) / (high - low)) * 100.0

    @staticmethod
    def _data_quality_status(row: dict) -> str:
        metrics = row.get("metrics", {})
        if float(metrics.get("networkKm", 0.0)) <= 0:
            return "fallbacked"
        if int(metrics.get("bicimadStationsCount", 0)) <= 0 or float(metrics.get("avgTrafficExposure", 0.0)) <= 0:
            return "partially_observed"
        return "fully_observed"

    @staticmethod
    def _data_quality_fallbacks(row: dict) -> list[str]:
        metrics = row.get("metrics", {})
        fallbacks = []
        if int(metrics.get("bicimadStationsCount", 0)) <= 0 and float(metrics.get("bicimadCoverage", 0.0)) <= 0:
            fallbacks.append("bicimad_without_local_coverage")
        if float(metrics.get("avgTrafficExposure", 0.0)) <= 0:
            fallbacks.append("low_traffic_signal_coverage")
        return fallbacks

    @staticmethod
    def _performance_flags(row: dict) -> list[str]:
        metrics = row.get("metrics", {})
        flags = []
        if float(metrics.get("hostileShare", 0.0)) >= 0.80:
            flags.append("high_hostile_share")
        if float(metrics.get("avgNightRisk", 0.0)) >= 0.70:
            flags.append("high_night_risk")
        if float(metrics.get("infraShare", 0.0)) <= 0.10:
            flags.append("low_bike_infrastructure_share")
        return flags

    @staticmethod
    def _normalization_flags(row: dict) -> list[str]:
        metrics = row.get("metrics", {})
        flags = []
        if float(metrics.get("networkKm", 0.0)) >= 2.0:
            for key in ("safety_score", "bike_infra_score", "low_hostility_score", "green_cyclable_score", "night_score", "junction_score"):
                if float(row.get(key, 0.0)) == 15.0:
                    flags.append(f"{key}_soft_floor_applied")
        return flags

    @staticmethod
    def _clamp01(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

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
