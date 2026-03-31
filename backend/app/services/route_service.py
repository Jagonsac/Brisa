import networkx as nx
import osmnx as ox

from app.schemas.route_response import RouteResponse
from app.services.geocoding_service import GeocodingService
from app.services.graph_service import GraphService
from app.utils.geojson import build_route_geojson_feature


class RouteService:
    def __init__(self, graph_service: GraphService | None = None, geocoding_service: GeocodingService | None = None) -> None:
        self.graph_service = graph_service or GraphService()
        self.geocoding_service = geocoding_service or GeocodingService()

    async def build_fastest_route(self, origin_query: str, destination_query: str, mode: str) -> RouteResponse:
        origin = await self.geocoding_service.geocode(origin_query)
        destination = await self.geocoding_service.geocode(destination_query)

        graph, graph_source = self.graph_service.get_graph()

        origin_node = ox.distance.nearest_nodes(graph, X=origin.lon, Y=origin.lat)
        destination_node = ox.distance.nearest_nodes(graph, X=destination.lon, Y=destination.lat)

        try:
            path = nx.shortest_path(graph, origin_node, destination_node, weight="length")
        except nx.NetworkXNoPath as error:
            raise ValueError("No encontramos una ruta ciclista entre los puntos indicados.") from error

        if len(path) < 2:
            raise ValueError("La ruta calculada no contiene segmentos válidos.")

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
                segment_coords = [[float(source["x"]), float(source["y"])], [float(target["x"]), float(target["y"])]]

            if coordinates and coordinates[-1] == segment_coords[0]:
                coordinates.extend(segment_coords[1:])
            else:
                coordinates.extend(segment_coords)

        if len(coordinates) < 2:
            raise ValueError("La ruta calculada no pudo serializarse correctamente.")

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
