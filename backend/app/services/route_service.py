import math
import threading

import networkx as nx
import numpy as np
import osmnx as ox

from app.core.routing_profiles import routing_profiles_config
from app.schemas.route_response import RouteResponse
from app.services.bicimad_service import BicimadService
from app.services.edge_weight_service import EdgeWeightService
from app.services.geocoding_service import GeocodedPoint, GeocodingError, GeocodingService
from app.services.graph_service import GraphService
from app.services.station_status_service import StationStatusService
from app.utils.geojson import build_route_geojson_feature


class RouteServiceError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class RouteService:
    def __init__(self, graph_service: GraphService | None = None, geocoding_service: GeocodingService | None = None) -> None:
        self.graph_service = graph_service or GraphService()
        self.geocoding_service = geocoding_service or GeocodingService()
        self.edge_weight_service = EdgeWeightService()
        self.bicimad_service = BicimadService()
        self.station_status_service = StationStatusService()
        self._weight_lock = threading.Lock()
        self._last_decorated_signature: tuple[int, str, int] | None = None

    async def build_route(
        self,
        origin_query: str,
        destination_query: str,
        mode: str,
        *,
        origin_lat: float | None = None,
        origin_lon: float | None = None,
        destination_lat: float | None = None,
        destination_lon: float | None = None,
        use_bicimad: bool = False,
    ) -> RouteResponse:
        origin = await self._resolve_point(query=origin_query, point_label="origen", lat=origin_lat, lon=origin_lon)
        destination = await self._resolve_point(query=destination_query, point_label="destino", lat=destination_lat, lon=destination_lon)

        if use_bicimad:
            return await self._build_bicimad_route(origin=origin, destination=destination, mode=mode)

        return self._build_bike_route(origin=origin, destination=destination, mode=mode)

    def _build_bike_route(self, *, origin: GeocodedPoint, destination: GeocodedPoint, mode: str) -> RouteResponse:
        graph, graph_source = self.graph_service.get_graph(network_type="bike")
        edge_weights_payload = self.edge_weight_service.get_edge_weights()
        edge_metrics = edge_weights_payload.get("edges", {})
        weight_name = f"brisa_weight_{mode}"
        self._ensure_graph_weights(graph, edge_metrics=edge_metrics, weights_version=edge_weights_payload.get("version", "v1"))

        try:
            origin_node = self._resolve_nearest_node(graph, lat=origin.lat, lon=origin.lon)
            destination_node = self._resolve_nearest_node(graph, lat=destination.lat, lon=destination.lon)
            leg = self._compute_path(graph, origin_node, destination_node, weight_name=weight_name, edge_metrics=edge_metrics)
        except nx.NetworkXNoPath as error:
            raise RouteServiceError("route_not_found", "No hemos encontrado una ruta válida entre esos puntos.") from error
        except Exception as error:
            raise RouteServiceError("snap_failed", "No se pudo ajustar el origen o destino a la red ciclista.") from error

        baseline_fastest = self._estimate_baseline_fastest(graph, origin_node, destination_node)
        explanations = self._build_explanations(
            mode=mode,
            distance_meters=leg["distance_meters"],
            baseline_fastest=baseline_fastest,
            avg_safety_risk=leg["avg_safety_risk"],
            avg_lighting_deficit=leg["avg_lighting_deficit"],
            avg_night_risk=leg["avg_night_risk"],
            avg_traffic=leg["avg_traffic"],
            avg_junction=leg["avg_junction"],
            avg_bike_infra=leg["avg_bike_infra"],
        )

        return RouteResponse.model_validate(
            {
                "data": {
                    "routeGeoJson": build_route_geojson_feature(
                        coordinates=leg["coordinates"],
                        distance_meters=leg["distance_meters"],
                        mode=mode,
                        profile="bike",
                    ),
                    "origin": {"query": origin.query, "displayName": origin.display_name, "lat": origin.lat, "lon": origin.lon},
                    "destination": {
                        "query": destination.query,
                        "displayName": destination.display_name,
                        "lat": destination.lat,
                        "lon": destination.lon,
                    },
                    "summary": {
                        "distanceMeters": round(leg["distance_meters"], 2),
                        "distanceKm": round(leg["distance_meters"] / 1000, 2),
                        "mode": mode,
                        "relativeSafety": self._label_for_safety(leg["avg_safety_risk"]),
                        "lightingQuality": self._label_for_lighting(leg["avg_lighting_deficit"]),
                        "nightRisk": self._label_for_night(leg["avg_night_risk"]),
                    },
                    "explanations": explanations,
                },
                "meta": {
                    "engine": "osmnx",
                    "graphSource": graph_source,
                    "weightProfile": mode,
                    "usedSafetyGrid": False,
                    "usedLightingGrid": False,
                    "usedNightRiskGrid": False,
                    "networkType": graph.graph.get("network_type", "bike_hardened"),
                },
            }
        )

    async def _build_bicimad_route(self, *, origin: GeocodedPoint, destination: GeocodedPoint, mode: str) -> RouteResponse:
        if self._haversine_meters(origin.lat, origin.lon, destination.lat, destination.lon) < 700:
            raise RouteServiceError("route_not_found", "El trayecto es demasiado corto para recomendar Bicimad.")

        station_response = await self.bicimad_service.get_stations(source_mode="auto")
        stations = station_response.data
        fallback_used = station_response.meta.fallbackUsed

        live_status_used = True
        try:
            status_by_id, _ = await self.station_status_service.get_status()
        except Exception:
            status_by_id = self.station_status_service.get_cached_status()
            live_status_used = False

        bike_graph, bike_graph_source = self.graph_service.get_graph(network_type="bike")
        walk_graph, walk_graph_source = self.graph_service.get_graph(network_type="walk")
        edge_weights_payload = self.edge_weight_service.get_edge_weights()
        edge_metrics = edge_weights_payload.get("edges", {})
        self._ensure_graph_weights(
            bike_graph,
            edge_metrics=edge_metrics,
            weights_version=edge_weights_payload.get("version", "v1"),
        )
        bike_weight_name = f"brisa_weight_{mode}"

        dep_candidates = self._pick_station_candidates(stations, status_by_id, origin, candidate_type="departure")
        arr_candidates = self._pick_station_candidates(stations, status_by_id, destination, candidate_type="arrival")

        if not dep_candidates:
            raise RouteServiceError("route_not_found", "No hay estaciones Bicimad de salida razonables cerca del origen.")
        if not arr_candidates:
            raise RouteServiceError("route_not_found", "No hay estaciones Bicimad de llegada razonables cerca del destino.")

        evaluated_pairs = 0
        best_plan = None

        for dep in dep_candidates[:5]:
            for arr in arr_candidates[:5]:
                if dep["station"].id == arr["station"].id:
                    continue
                evaluated_pairs += 1
                try:
                    walk1 = self._compute_walk_leg(walk_graph, origin.lat, origin.lon, dep["station"].lat, dep["station"].lon)
                    bike_leg = self._compute_bike_leg(bike_graph, edge_metrics, bike_weight_name, dep["station"].lat, dep["station"].lon, arr["station"].lat, arr["station"].lon)
                    walk2 = self._compute_walk_leg(walk_graph, arr["station"].lat, arr["station"].lon, destination.lat, destination.lon)
                except Exception:
                    continue

                walk_duration = walk1["duration_seconds"] + walk2["duration_seconds"]
                bike_duration = bike_leg["duration_seconds"]
                score = self._multimodal_score(
                    mode=mode,
                    walk_duration_seconds=walk_duration,
                    bike_duration_seconds=bike_duration,
                    dep_status=dep["status"],
                    arr_status=arr["status"],
                )

                if bike_leg["distance_meters"] < 500:
                    score += 900

                plan = {
                    "dep": dep,
                    "arr": arr,
                    "walk1": walk1,
                    "walk2": walk2,
                    "bike": bike_leg,
                    "score": score,
                }
                if best_plan is None or score < best_plan["score"]:
                    best_plan = plan

        if best_plan is None:
            raise RouteServiceError("route_not_found", "No se encontró una combinación multimodal Bicimad válida.")

        walk_distance = best_plan["walk1"]["distance_meters"] + best_plan["walk2"]["distance_meters"]
        walk_duration = best_plan["walk1"]["duration_seconds"] + best_plan["walk2"]["duration_seconds"]
        bike_distance = best_plan["bike"]["distance_meters"]
        bike_duration = best_plan["bike"]["duration_seconds"]
        total_distance = walk_distance + bike_distance
        total_duration = walk_duration + bike_duration

        all_coordinates = (
            best_plan["walk1"]["coordinates"]
            + best_plan["bike"]["coordinates"][1:]
            + best_plan["walk2"]["coordinates"][1:]
        )

        explanations = [
            "Se recomienda esta estación de salida por equilibrio entre cercanía y bicicletas disponibles.",
            "La estación final prioriza anclajes disponibles y reduce el paseo final.",
            f"El tramo en bici mantiene el perfil '{mode}' seleccionado.",
        ]

        return RouteResponse.model_validate(
            {
                "data": {
                    "routeGeoJson": build_route_geojson_feature(
                        coordinates=all_coordinates,
                        distance_meters=total_distance,
                        mode="bicimad",
                        profile="multimodal",
                    ),
                    "origin": {"query": origin.query, "displayName": origin.display_name, "lat": origin.lat, "lon": origin.lon},
                    "destination": {
                        "query": destination.query,
                        "displayName": destination.display_name,
                        "lat": destination.lat,
                        "lon": destination.lon,
                    },
                    "bikeProfile": mode,
                    "transportMode": "bicimad",
                    "stations": {
                        "departure": self._station_payload(best_plan["dep"]),
                        "arrival": self._station_payload(best_plan["arr"]),
                    },
                    "segments": [
                        {
                            "type": "walk",
                            "from": "origin",
                            "to": "departure_station",
                            "distanceMeters": round(best_plan["walk1"]["distance_meters"], 2),
                            "durationSeconds": round(best_plan["walk1"]["duration_seconds"], 1),
                            "geometry": {"type": "LineString", "coordinates": best_plan["walk1"]["coordinates"]},
                        },
                        {
                            "type": "bike",
                            "profile": mode,
                            "from": "departure_station",
                            "to": "arrival_station",
                            "distanceMeters": round(bike_distance, 2),
                            "durationSeconds": round(bike_duration, 1),
                            "geometry": {"type": "LineString", "coordinates": best_plan["bike"]["coordinates"]},
                            "explanations": self._build_explanations(
                                mode=mode,
                                distance_meters=bike_distance,
                                baseline_fastest=bike_distance,
                                avg_safety_risk=best_plan["bike"]["avg_safety_risk"],
                                avg_lighting_deficit=best_plan["bike"]["avg_lighting_deficit"],
                                avg_night_risk=best_plan["bike"]["avg_night_risk"],
                                avg_traffic=best_plan["bike"]["avg_traffic"],
                                avg_junction=best_plan["bike"]["avg_junction"],
                                avg_bike_infra=best_plan["bike"]["avg_bike_infra"],
                            ),
                        },
                        {
                            "type": "walk",
                            "from": "arrival_station",
                            "to": "destination",
                            "distanceMeters": round(best_plan["walk2"]["distance_meters"], 2),
                            "durationSeconds": round(best_plan["walk2"]["duration_seconds"], 1),
                            "geometry": {"type": "LineString", "coordinates": best_plan["walk2"]["coordinates"]},
                        },
                    ],
                    "summary": {
                        "distanceMeters": round(total_distance, 2),
                        "distanceKm": round(total_distance / 1000, 2),
                        "mode": "bicimad",
                        "relativeSafety": self._label_for_safety(best_plan["bike"]["avg_safety_risk"]),
                        "lightingQuality": self._label_for_lighting(best_plan["bike"]["avg_lighting_deficit"]),
                        "nightRisk": self._label_for_night(best_plan["bike"]["avg_night_risk"]),
                        "estimatedDurationMinutes": round(total_duration / 60, 1),
                        "totalDurationSeconds": round(total_duration, 1),
                        "walkDistanceMeters": round(walk_distance, 2),
                        "walkDurationSeconds": round(walk_duration, 1),
                        "bikeDistanceMeters": round(bike_distance, 2),
                        "bikeDurationSeconds": round(bike_duration, 1),
                    },
                    "explanations": explanations,
                },
                "meta": {
                    "engine": "osmnx",
                    "graphSource": "cache" if bike_graph_source == "cache" and walk_graph_source == "cache" else "download",
                    "weightProfile": mode,
                    "usedSafetyGrid": False,
                    "usedLightingGrid": False,
                    "usedNightRiskGrid": False,
                    "networkType": "multimodal",
                    "liveStatusUsed": live_status_used,
                    "fallbackUsed": fallback_used,
                    "evaluatedPairs": evaluated_pairs,
                },
            }
        )

    def _compute_walk_leg(self, graph, lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> dict:
        node_a = self._resolve_nearest_node(graph, lat=lat_a, lon=lon_a)
        node_b = self._resolve_nearest_node(graph, lat=lat_b, lon=lon_b)
        leg = self._compute_path(graph, node_a, node_b, weight_name="length", edge_metrics={})
        walking_speed_mps = 1.32
        leg["duration_seconds"] = leg["distance_meters"] / walking_speed_mps
        return leg

    def _compute_bike_leg(self, graph, edge_metrics: dict, weight_name: str, lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> dict:
        node_a = self._resolve_nearest_node(graph, lat=lat_a, lon=lon_a)
        node_b = self._resolve_nearest_node(graph, lat=lat_b, lon=lon_b)
        leg = self._compute_path(graph, node_a, node_b, weight_name=weight_name, edge_metrics=edge_metrics)
        bike_speed_mps = 4.2
        leg["duration_seconds"] = leg["distance_meters"] / bike_speed_mps
        return leg

    def _compute_path(self, graph, origin_node, destination_node, *, weight_name: str, edge_metrics: dict) -> dict:
        path = nx.shortest_path(graph, origin_node, destination_node, weight=weight_name)
        coordinates: list[list[float]] = []
        distance_meters = 0.0
        route_day_risk = []
        route_lighting = []
        route_night = []
        route_traffic = []
        route_junction = []
        route_bike_infra = []

        for index in range(len(path) - 1):
            source_node = path[index]
            target_node = path[index + 1]
            edge_data = graph.get_edge_data(source_node, target_node)
            if not edge_data:
                continue
            best_key, best_edge = min(edge_data.items(), key=lambda pair: pair[1].get(weight_name, pair[1].get("length", float("inf"))))
            edge_id = f"{source_node}:{target_node}:{best_key}"
            metrics = edge_metrics.get(edge_id, {})
            distance_meters += float(best_edge.get("length", 0.0))
            route_day_risk.append(float(metrics.get("safetyRiskNormalized", 0.45)))
            route_lighting.append(float(metrics.get("lightingDeficitNormalized", 0.5)))
            route_night.append(float(metrics.get("nightRiskNormalized", 0.35)))
            route_traffic.append(float(metrics.get("motorTrafficExposureScore", 0.35)))
            route_junction.append(float(metrics.get("junctionComplexityScore", 0.35)))
            route_bike_infra.append(float(metrics.get("bikeInfrastructureScore", 0.25)))

            if "geometry" in best_edge:
                segment_coords = [[float(lon), float(lat)] for lon, lat in best_edge["geometry"].coords]
            else:
                source = graph.nodes[source_node]
                target = graph.nodes[target_node]
                segment_coords = [[float(source["x"]), float(source["y"])], [float(target["x"]), float(target["y"])]]

            if coordinates and coordinates[-1] == segment_coords[0]:
                coordinates.extend(segment_coords[1:])
            else:
                coordinates.extend(segment_coords)

        if len(coordinates) < 2:
            raise RouteServiceError("route_not_found", "No hemos encontrado una ruta válida entre esos puntos.")

        return {
            "coordinates": coordinates,
            "distance_meters": distance_meters,
            "avg_safety_risk": round(sum(route_day_risk) / len(route_day_risk), 4) if route_day_risk else 0.45,
            "avg_lighting_deficit": round(sum(route_lighting) / len(route_lighting), 4) if route_lighting else 0.5,
            "avg_night_risk": round(sum(route_night) / len(route_night), 4) if route_night else 0.35,
            "avg_traffic": round(sum(route_traffic) / len(route_traffic), 4) if route_traffic else 0.35,
            "avg_junction": round(sum(route_junction) / len(route_junction), 4) if route_junction else 0.35,
            "avg_bike_infra": round(sum(route_bike_infra) / len(route_bike_infra), 4) if route_bike_infra else 0.25,
        }

    def _pick_station_candidates(self, stations, status_by_id: dict, point: GeocodedPoint, *, candidate_type: str) -> list[dict]:
        candidates = []
        for station in stations:
            distance = self._haversine_meters(point.lat, point.lon, station.lat, station.lon)
            if distance > 1500:
                continue
            status = status_by_id.get(station.id, {})
            is_operational = status.get("isInstalled", True) and (status.get("isRenting", True) or status.get("isReturning", True))
            if not is_operational:
                continue
            availability = status.get("bikesAvailable") if candidate_type == "departure" else status.get("docksAvailable")
            if availability == 0:
                continue
            score = distance + (0 if availability is None else max(0, 5 - availability) * 120)
            candidates.append({"station": station, "status": status, "distance": distance, "score": score})

        candidates.sort(key=lambda item: item["score"])
        return candidates[:8]

    def _multimodal_score(self, *, mode: str, walk_duration_seconds: float, bike_duration_seconds: float, dep_status: dict, arr_status: dict) -> float:
        if mode == "fastest":
            walk_w, bike_w = 1.0, 1.3
        elif mode in {"safe", "night"}:
            walk_w, bike_w = 0.85, 1.35
        else:
            walk_w, bike_w = 1.0, 1.1

        bikes_penalty = 0 if dep_status.get("bikesAvailable") is None else max(0, 3 - int(dep_status.get("bikesAvailable", 0))) * 180
        docks_penalty = 0 if arr_status.get("docksAvailable") is None else max(0, 3 - int(arr_status.get("docksAvailable", 0))) * 180
        return walk_duration_seconds * walk_w + bike_duration_seconds * bike_w + bikes_penalty + docks_penalty

    def _station_payload(self, station_bundle: dict) -> dict:
        station = station_bundle["station"]
        status = station_bundle["status"]
        return {
            "stationId": station.id,
            "name": station.name,
            "lat": station.lat,
            "lon": station.lon,
            "bikesAvailable": status.get("bikesAvailable"),
            "docksAvailable": status.get("docksAvailable"),
            "isOperational": bool(status.get("isInstalled", True)),
        }

    def _decorate_graph_weights(self, graph, *, edge_metrics: dict) -> None:
        for u, v, key, data in graph.edges(keys=True, data=True):
            length = float(data.get("length") or 0.0)
            edge_id = f"{u}:{v}:{key}"
            metrics = edge_metrics.get(edge_id, {})
            safety = float(metrics.get("safetyRiskNormalized", 0.45))
            lighting = float(metrics.get("lightingDeficitNormalized", 0.5))
            night = float(metrics.get("nightRiskNormalized", 0.35))
            hostility = float(metrics.get("roadHostilityScore", 0.5))

            data["brisa_weight_fastest"] = length * (1 + routing_profiles_config.fastest_extreme_hostility_multiplier * max(0.0, hostility - 0.85))
            data["brisa_weight_safe"] = length * (1 + routing_profiles_config.safe_risk_multiplier * safety)
            data["brisa_weight_balanced"] = length * (1 + routing_profiles_config.balanced_risk_multiplier * safety)
            data["brisa_weight_night"] = length * (
                1
                + routing_profiles_config.night_base_risk_multiplier * safety
                + routing_profiles_config.night_lighting_multiplier * lighting
                + routing_profiles_config.night_accident_multiplier * night
            )

    def _ensure_graph_weights(self, graph, *, edge_metrics: dict, weights_version: str) -> None:
        graph_signature = (id(graph), weights_version, len(edge_metrics))
        if self._last_decorated_signature == graph_signature:
            return
        with self._weight_lock:
            if self._last_decorated_signature == graph_signature:
                return
            self._decorate_graph_weights(graph, edge_metrics=edge_metrics)
            self._last_decorated_signature = graph_signature

    @staticmethod
    def _estimate_baseline_fastest(graph, origin_node, destination_node) -> float:
        try:
            return float(nx.shortest_path_length(graph, origin_node, destination_node, weight="length"))
        except nx.NetworkXNoPath:
            return 0.0

    def warmup_routing_engine(self) -> None:
        graph, _ = self.graph_service.get_graph(network_type="bike")
        self.graph_service.get_graph(network_type="walk")
        edge_weights_payload = self.edge_weight_service.get_edge_weights()
        self._ensure_graph_weights(graph, edge_metrics=edge_weights_payload.get("edges", {}), weights_version=edge_weights_payload.get("version", "v1"))

    def _build_explanations(self, *, mode: str, distance_meters: float, baseline_fastest: float, avg_safety_risk: float, avg_lighting_deficit: float, avg_night_risk: float, avg_traffic: float, avg_junction: float, avg_bike_infra: float) -> list[str]:
        distance_delta = round(distance_meters - baseline_fastest, 1) if baseline_fastest else 0.0
        if mode == "fastest":
            return [
                "Ruta optimizada por tiempo/distancia, manteniendo filtros de legalidad ciclista.",
                "Solo penaliza tramos con hostilidad extrema para evitar calzadas especialmente adversas.",
            ]

        if mode == "balanced":
            return [
                "Reduce exposición a tráfico motorizado intenso sin forzar desvíos extremos.",
                f"Compromiso seguridad-distancia con riesgo diurno medio {int(avg_safety_risk * 100)}/100.",
                "Prioriza infraestructura ciclista cuando existe un corredor alternativo razonable.",
            ]

        if mode == "safe":
            extra = f"Acepta {round(distance_delta/1000, 2)} km extra" if distance_delta > 150 else "Mantiene desvío contenido"
            return [
                f"{extra} para evitar arterias con muchos carriles y alta exposición al tráfico.",
                f"Reduce cruces complejos (índice {int(avg_junction*100)}/100) y concentra tramos más ciclables.",
                f"Prioriza infraestructura ciclista oficial/OSM (score medio {int(avg_bike_infra*100)}/100).",
            ]

        return [
            "En modo nocturno prioriza tramos mejor iluminados y minimiza zonas con déficit de farolas.",
            f"Penaliza comportamiento histórico nocturno ({int(avg_night_risk*100)}/100) y exposición motorizada.",
            "Evita intersecciones complejas de noche salvo que no exista alternativa ciclable razonable.",
        ]

    @staticmethod
    def _label_for_safety(avg_safety_risk: float) -> str:
        if avg_safety_risk <= 0.33:
            return "high"
        if avg_safety_risk <= 0.66:
            return "medium"
        return "low"

    @staticmethod
    def _label_for_lighting(avg_lighting_deficit: float) -> str:
        if avg_lighting_deficit <= 0.33:
            return "high"
        if avg_lighting_deficit <= 0.66:
            return "medium"
        return "low"

    @staticmethod
    def _label_for_night(avg_night_risk: float) -> str:
        if avg_night_risk <= 0.33:
            return "low"
        if avg_night_risk <= 0.66:
            return "medium"
        return "high"

    async def _resolve_point(self, *, query: str, point_label: str, lat: float | None, lon: float | None) -> GeocodedPoint:
        clean_query = query.strip()
        if lat is not None and lon is not None:
            return GeocodedPoint(query=clean_query, display_name=clean_query or f"{point_label.title()} seleccionado", lat=lat, lon=lon)
        try:
            return await self.geocoding_service.geocode(clean_query, point_label=point_label)
        except GeocodingError as error:
            raise RouteServiceError(error.code, error.message) from error

    def _resolve_nearest_node(self, graph, *, lat: float, lon: float):
        try:
            return ox.distance.nearest_nodes(graph, X=lon, Y=lat)
        except (ImportError, ModuleNotFoundError):
            return self._resolve_nearest_node_fallback(graph, lat=lat, lon=lon)

    def _resolve_nearest_node_fallback(self, graph, *, lat: float, lon: float):
        node_ids = list(graph.nodes)
        node_coordinates = np.array([[float(graph.nodes[node]["y"]), float(graph.nodes[node]["x"])] for node in node_ids])
        target = np.array([lat, lon], dtype=float)
        deltas = node_coordinates - target
        squared_distances = np.einsum("ij,ij->i", deltas, deltas)
        return node_ids[int(np.argmin(squared_distances))]

    @staticmethod
    def _haversine_meters(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
        radius = 6371000
        phi_1 = math.radians(lat_a)
        phi_2 = math.radians(lat_b)
        d_phi = math.radians(lat_b - lat_a)
        d_lambda = math.radians(lon_b - lon_a)
        a = math.sin(d_phi / 2) ** 2 + math.cos(phi_1) * math.cos(phi_2) * math.sin(d_lambda / 2) ** 2
        return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))
