from pathlib import Path
import threading

import networkx as nx
import osmnx as ox
from networkx import MultiDiGraph
from xml.etree.ElementTree import ParseError

from app.core.config import settings
from app.services.bike_legality_service import evaluate_bike_legality


class GraphService:
    _shared_graphs: dict[str, MultiDiGraph] = {}
    _shared_graph_sources: dict[str, str] = {}
    _shared_lock = threading.Lock()

    @classmethod
    def clear_shared_cache(cls, network_types: set[str] | None = None) -> None:
        with cls._shared_lock:
            if network_types is None:
                cls._shared_graphs.clear()
                cls._shared_graph_sources.clear()
                return

            for network_type in network_types:
                cls._shared_graphs.pop(network_type, None)
                cls._shared_graph_sources.pop(network_type, None)

    def __init__(self) -> None:
        self.graphs_dir = Path(__file__).resolve().parents[2] / "data" / "graphs"
        self.graph_path = self.graphs_dir / settings.osmnx_graph_filename
        self.filtered_graph_path = self.graphs_dir / f"filtered_{settings.osmnx_graph_filename}"

    def get_graph(self, network_type: str = "bike") -> tuple[MultiDiGraph, str]:
        if network_type in GraphService._shared_graphs:
            return GraphService._shared_graphs[network_type], GraphService._shared_graph_sources.get(network_type, "cache")

        with GraphService._shared_lock:
            if network_type in GraphService._shared_graphs:
                return GraphService._shared_graphs[network_type], GraphService._shared_graph_sources.get(network_type, "cache")

            self.graphs_dir.mkdir(parents=True, exist_ok=True)
            return self._load_graph_by_network(network_type)

    def _load_graph_by_network(self, network_type: str) -> tuple[MultiDiGraph, str]:
        if network_type == "walk":
            walk_path = self.graphs_dir / "madrid_walk.graphml"
            if walk_path.exists():
                cached = self._try_load_graph(walk_path)
                if cached is not None:
                    GraphService._shared_graphs["walk"] = cached
                    GraphService._shared_graph_sources["walk"] = "cache"
                    return cached, "cache"

            graph = ox.graph_from_place(settings.osmnx_place_query, network_type="walk", simplify=True)
            graph.graph["network_type"] = "walk"
            ox.save_graphml(graph, walk_path)
            GraphService._shared_graphs["walk"] = graph
            GraphService._shared_graph_sources["walk"] = "download"
            return graph, "download"

        if self.filtered_graph_path.exists():
            cached = self._try_load_graph(self.filtered_graph_path)
            if cached is not None and cached.graph.get("brisa_filtered"):
                GraphService._shared_graphs["bike"] = cached
                GraphService._shared_graph_sources["bike"] = "cache"
                return cached, "cache"

        base_graph = self._load_or_download_base_graph()
        filtered_graph = self._build_filtered_graph(base_graph)
        ox.save_graphml(filtered_graph, self.filtered_graph_path)

        GraphService._shared_graphs["bike"] = filtered_graph
        GraphService._shared_graph_sources["bike"] = "download"
        return filtered_graph, "download"

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
