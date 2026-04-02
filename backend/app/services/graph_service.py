from pathlib import Path
import threading

import networkx as nx
import osmnx as ox
from networkx import MultiDiGraph
from xml.etree.ElementTree import ParseError

from app.core.config import settings
from app.services.bike_legality_service import evaluate_bike_legality


class GraphService:
    _shared_graph: MultiDiGraph | None = None
    _shared_graph_source: str = "cache"
    _shared_lock = threading.Lock()

    def __init__(self) -> None:
        self.graphs_dir = Path(__file__).resolve().parents[2] / "data" / "graphs"
        self.graph_path = self.graphs_dir / settings.osmnx_graph_filename
        self.filtered_graph_path = self.graphs_dir / f"filtered_{settings.osmnx_graph_filename}"

    def get_graph(self) -> tuple[MultiDiGraph, str]:
        if GraphService._shared_graph is not None:
            return GraphService._shared_graph, GraphService._shared_graph_source

        with GraphService._shared_lock:
            if GraphService._shared_graph is not None:
                return GraphService._shared_graph, GraphService._shared_graph_source

            self.graphs_dir.mkdir(parents=True, exist_ok=True)
            if self.filtered_graph_path.exists():
                cached = self._try_load_graph(self.filtered_graph_path)
                if cached is not None and cached.graph.get("brisa_filtered"):
                    GraphService._shared_graph = cached
                    GraphService._shared_graph_source = "cache"
                    return cached, GraphService._shared_graph_source

            base_graph = self._load_or_download_base_graph()
            filtered_graph = self._build_filtered_graph(base_graph)
            ox.save_graphml(filtered_graph, self.filtered_graph_path)

            GraphService._shared_graph = filtered_graph
            GraphService._shared_graph_source = "download"
            return filtered_graph, GraphService._shared_graph_source

    def _load_or_download_base_graph(self) -> MultiDiGraph:
        if self.graph_path.exists():
            cached_graph = self._try_load_graph(self.graph_path)
            if cached_graph is not None and self._is_expected_network(cached_graph):
                return cached_graph

        try:
            graph = ox.graph_from_place(settings.osmnx_place_query, network_type=settings.osmnx_network_type, simplify=True)
            ox.save_graphml(graph, self.graph_path)
            return graph
        except Exception as error:
            raise RuntimeError("No se pudo preparar el grafo de rutas.") from error

    def _try_load_graph(self, path: Path) -> MultiDiGraph | None:
        try:
            return ox.load_graphml(path)
        except (ParseError, ValueError, OSError):
            path.unlink(missing_ok=True)
            return None

    def _build_filtered_graph(self, graph: MultiDiGraph) -> MultiDiGraph:
        filtered = nx.MultiDiGraph()
        filtered.graph.update(graph.graph)
        filtered.graph["brisa_filtered"] = True

        filtered.add_nodes_from(graph.nodes(data=True))

        blocked_edges = 0
        for u, v, key, data in graph.edges(keys=True, data=True):
            decision = evaluate_bike_legality(data)
            if not decision.allowed:
                blocked_edges += 1
                continue
            filtered.add_edge(u, v, key=key, **data)

        isolated_nodes = [node for node, degree in filtered.degree() if degree == 0]
        filtered.remove_nodes_from(isolated_nodes)
        filtered.graph["blocked_edges"] = blocked_edges
        filtered.graph["network_type"] = "bike_hardened"
        return filtered

    def _is_expected_network(self, graph: MultiDiGraph) -> bool:
        network_type = graph.graph.get("network_type")
        return network_type in {settings.osmnx_network_type, "bike_hardened"}
