import json

import networkx as nx
import numpy as np
import osmnx as ox

from app.core.routing_profiles import routing_profiles_config
from app.schemas.route_response import RouteResponse
from app.services.edge_weight_service import EdgeWeightService
from app.services.geocoding_service import GeocodedPoint, GeocodingError, GeocodingService
from app.services.graph_service import GraphService
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
    ) -> RouteResponse:
        origin = await self._resolve_point(query=origin_query, point_label="origen", lat=origin_lat, lon=origin_lon)
        destination = await self._resolve_point(query=destination_query, point_label="destino", lat=destination_lat, lon=destination_lon)

        try:
            graph, graph_source = self.graph_service.get_graph()
        except RuntimeError as error:
            raise RouteServiceError(
                "graph_warming_up",
                "La red ciclista aún se está preparando. Inténtalo de nuevo en unos segundos.",
            ) from error

        edge_weights_payload = self.edge_weight_service.get_edge_weights()
        edge_metrics = edge_weights_payload.get("edges", {})

        try:
            origin_node = self._resolve_nearest_node(graph, lat=origin.lat, lon=origin.lon)
            destination_node = self._resolve_nearest_node(graph, lat=destination.lat, lon=destination.lon)
        except Exception as error:
            raise RouteServiceError("snap_failed", "No se pudo ajustar el origen o destino a la red ciclista.") from error

        weight_name = f"brisa_weight_{mode}"
        self._decorate_graph_weights(graph, edge_metrics=edge_metrics, mode=mode)

        try:
            path = nx.shortest_path(graph, origin_node, destination_node, weight=weight_name)
        except nx.NetworkXNoPath as error:
            raise RouteServiceError("route_not_found", "No hemos encontrado una ruta válida entre esos puntos.") from error

        if len(path) < 2:
            raise RouteServiceError("route_not_found", "No hemos encontrado una ruta válida entre esos puntos.")

        coordinates: list[list[float]] = []
        distance_meters = 0.0
        route_safety = []
        route_lighting = []
        route_night = []

        for index in range(len(path) - 1):
            source_node = path[index]
            target_node = path[index + 1]
            edge_data = graph.get_edge_data(source_node, target_node)
            if not edge_data:
                continue

            best_key, best_edge = min(edge_data.items(), key=lambda pair: pair[1].get(weight_name, float("inf")))
            edge_id = f"{source_node}:{target_node}:{best_key}"
            metrics = edge_metrics.get(edge_id, {})

            distance_meters += float(best_edge.get("length", 0.0))
            route_safety.append(float(metrics.get("safetyRiskNormalized", 0.45)))
            route_lighting.append(float(metrics.get("lightingDeficitNormalized", 0.5)))
            route_night.append(float(metrics.get("nightRiskNormalized", 0.35)))

            if "geometry" in best_edge:
                line = best_edge["geometry"]
                segment_coords = [[float(lon), float(lat)] for lon, lat in line.coords]
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

        avg_safety_risk = round(sum(route_safety) / len(route_safety), 4) if route_safety else 0.45
        avg_lighting_deficit = round(sum(route_lighting) / len(route_lighting), 4) if route_lighting else 0.5
        avg_night_risk = round(sum(route_night) / len(route_night), 4) if route_night else 0.35
        baseline_fastest = self._estimate_baseline_fastest(graph, origin_node, destination_node)
        explanations = self._build_explanations(
            mode=mode,
            distance_meters=distance_meters,
            baseline_fastest=baseline_fastest,
            avg_safety_risk=avg_safety_risk,
            avg_lighting_deficit=avg_lighting_deficit,
            avg_night_risk=avg_night_risk,
        )

        response_payload = {
            "data": {
                "routeGeoJson": build_route_geojson_feature(
                    coordinates=coordinates,
                    distance_meters=distance_meters,
                    mode=mode,
                    profile="bike",
                ),
                "origin": {
                    "query": origin.query,
                    "displayName": origin.display_name,
                    "lat": origin.lat,
                    "lon": origin.lon,
                },
                "destination": {
                    "query": destination.query,
                    "displayName": destination.display_name,
                    "lat": destination.lat,
                    "lon": destination.lon,
                },
                "summary": {
                    "distanceMeters": round(distance_meters, 2),
                    "distanceKm": round(distance_meters / 1000, 2),
                    "mode": mode,
                    "relativeSafety": self._label_for_safety(avg_safety_risk),
                    "lightingQuality": self._label_for_lighting(avg_lighting_deficit),
                    "nightRisk": self._label_for_night(avg_night_risk),
                },
                "explanations": explanations,
            },
            "meta": {
                "engine": "osmnx",
                "graphSource": graph_source,
                "weightProfile": mode,
                "usedSafetyGrid": mode in {"safe", "balanced", "night"},
                "usedLightingGrid": mode == "night",
                "usedNightRiskGrid": mode == "night",
                "networkType": graph.graph.get("network_type", "bike"),
            },
        }
        return RouteResponse.model_validate(response_payload)

    def _decorate_graph_weights(self, graph, *, edge_metrics: dict, mode: str) -> None:
        for u, v, key, data in graph.edges(keys=True, data=True):
            length = float(data.get("length") or 0.0)
            edge_id = f"{u}:{v}:{key}"
            metrics = edge_metrics.get(edge_id, {})
            safety = float(metrics.get("safetyRiskNormalized", 0.45))
            lighting = float(metrics.get("lightingDeficitNormalized", 0.5))
            night = float(metrics.get("nightRiskNormalized", 0.35))

            data["brisa_weight_fastest"] = length
            data["brisa_weight_safe"] = length * (1 + routing_profiles_config.safe_risk_multiplier * safety)
            data["brisa_weight_balanced"] = length * (1 + routing_profiles_config.balanced_risk_multiplier * safety)
            data["brisa_weight_night"] = length * (
                1
                + routing_profiles_config.night_base_risk_multiplier * safety
                + routing_profiles_config.night_lighting_multiplier * lighting
                + routing_profiles_config.night_accident_multiplier * night
            )

    @staticmethod
    def _estimate_baseline_fastest(graph, origin_node, destination_node) -> float:
        try:
            baseline_path = nx.shortest_path(graph, origin_node, destination_node, weight="length")
        except nx.NetworkXNoPath:
            return 0.0

        baseline_distance = 0.0
        for index in range(len(baseline_path) - 1):
            source = baseline_path[index]
            target = baseline_path[index + 1]
            edges = graph.get_edge_data(source, target)
            if not edges:
                continue
            best = min(edges.values(), key=lambda edge: edge.get("length", float("inf")))
            baseline_distance += float(best.get("length", 0.0))
        return baseline_distance

    def _build_explanations(
        self,
        *,
        mode: str,
        distance_meters: float,
        baseline_fastest: float,
        avg_safety_risk: float,
        avg_lighting_deficit: float,
        avg_night_risk: float,
    ) -> list[str]:
        distance_delta = round(distance_meters - baseline_fastest, 1) if baseline_fastest else 0.0

        if mode == "fastest":
            return [
                "Ruta optimizada por distancia para llegar lo antes posible.",
                "No aplica penalizaciones extra de seguridad o noche en este modo.",
            ]

        messages = []
        if mode == "safe":
            if distance_delta > 150:
                messages.append(f"Acepta {round(distance_delta / 1000, 2)} km extra para reducir exposición a zonas de mayor riesgo.")
            messages.append("Prioriza tramos con mejor score de seguridad ciclista del grid de Slice 5.")
            messages.append(f"Riesgo medio estimado del recorrido: {int(round(avg_safety_risk * 100))}/100.")
        elif mode == "balanced":
            messages.append("Combina distancia y seguridad para evitar desvíos excesivos.")
            if distance_delta > 0:
                messages.append(f"Incremento de distancia moderado frente a la más rápida: {round(distance_delta / 1000, 2)} km.")
            messages.append(f"Riesgo medio estimado equilibrado: {int(round(avg_safety_risk * 100))}/100.")
        elif mode == "night":
            messages.append("Prioriza calles mejor iluminadas usando densidad de farolas por celda.")
            messages.append(
                f"Penaliza zonas con peor iluminación ({int(round(avg_lighting_deficit * 100))}/100 de déficit medio) y accidentalidad nocturna."
            )
            messages.append(f"Riesgo nocturno agregado estimado: {int(round(avg_night_risk * 100))}/100.")

        return messages[:3]

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
            display_name = clean_query or f"{point_label.title()} seleccionado"
            return GeocodedPoint(query=clean_query, display_name=display_name, lat=lat, lon=lon)

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
        if not node_ids:
            raise ValueError("El grafo no contiene nodos.")

        node_coordinates = np.array([[float(graph.nodes[node]["y"]), float(graph.nodes[node]["x"])] for node in node_ids])
        target = np.array([lat, lon], dtype=float)
        deltas = node_coordinates - target
        squared_distances = np.einsum("ij,ij->i", deltas, deltas)
        nearest_index = int(np.argmin(squared_distances))
        return node_ids[nearest_index]
