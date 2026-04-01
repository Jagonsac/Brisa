import networkx as nx
import numpy as np
import osmnx as ox

from app.schemas.route_response import RouteResponse
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

    async def build_fastest_route(
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
        origin = await self._resolve_point(
            query=origin_query,
            point_label="origen",
            lat=origin_lat,
            lon=origin_lon,
        )
        destination = await self._resolve_point(
            query=destination_query,
            point_label="destino",
            lat=destination_lat,
            lon=destination_lon,
        )

        try:
            graph, graph_source = self.graph_service.get_graph()
        except RuntimeError as error:
            raise RouteServiceError(
                "graph_warming_up",
                "La red ciclista aún se está preparando. Inténtalo de nuevo en unos segundos.",
            ) from error

        try:
            origin_node = self._resolve_nearest_node(graph, lat=origin.lat, lon=origin.lon)
            destination_node = self._resolve_nearest_node(graph, lat=destination.lat, lon=destination.lon)
        except Exception as error:
            raise RouteServiceError("snap_failed", "No se pudo ajustar el origen o destino a la red ciclista.") from error

        try:
            path = nx.shortest_path(graph, origin_node, destination_node, weight="length")
        except nx.NetworkXNoPath as error:
            raise RouteServiceError("route_not_found", "No hemos encontrado una ruta válida entre esos puntos.") from error

        if len(path) < 2:
            raise RouteServiceError("route_not_found", "No hemos encontrado una ruta válida entre esos puntos.")

        coordinates: list[list[float]] = []
        distance_meters = 0.0

        for index in range(len(path) - 1):
            source_node = path[index]
            target_node = path[index + 1]
            edge_data = graph.get_edge_data(source_node, target_node)
            if not edge_data:
                continue

            best_edge = min(edge_data.values(), key=lambda edge: edge.get("length", float("inf")))
            distance_meters += float(best_edge.get("length", 0.0))

            if "geometry" in best_edge:
                line = best_edge["geometry"]
                segment_coords = [[float(lon), float(lat)] for lon, lat in line.coords]
            else:
                source = graph.nodes[source_node]
                target = graph.nodes[target_node]
                segment_coords = [[float(source["x"]), float(source["y"])], [float(target["x"]), float(target["y"])] ]

            if coordinates and coordinates[-1] == segment_coords[0]:
                coordinates.extend(segment_coords[1:])
            else:
                coordinates.extend(segment_coords)

        if len(coordinates) < 2:
            raise RouteServiceError("route_not_found", "No hemos encontrado una ruta válida entre esos puntos.")

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
                },
            },
            "meta": {
                "source": "osmnx",
                "graphSource": graph_source,
                "weight": "length",
                "networkType": graph.graph.get("network_type", "bike"),
            },
        }
        return RouteResponse.model_validate(response_payload)

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
