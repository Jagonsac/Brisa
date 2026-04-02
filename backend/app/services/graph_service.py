from pathlib import Path
import threading

import osmnx as ox
from networkx import MultiDiGraph
from xml.etree.ElementTree import ParseError

from app.core.config import settings


class GraphService:
    _shared_graph: MultiDiGraph | None = None
    _shared_graph_source: str = "cache"
    _shared_lock = threading.Lock()

    def __init__(self) -> None:
        self.graphs_dir = Path(__file__).resolve().parents[2] / "data" / "graphs"
        self.graph_path = self.graphs_dir / settings.osmnx_graph_filename

    def get_graph(self) -> tuple[MultiDiGraph, str]:
        if GraphService._shared_graph is not None:
            return GraphService._shared_graph, GraphService._shared_graph_source

        with GraphService._shared_lock:
            if GraphService._shared_graph is not None:
                return GraphService._shared_graph, GraphService._shared_graph_source

            self.graphs_dir.mkdir(parents=True, exist_ok=True)
            if self.graph_path.exists():
                try:
                    cached_graph = ox.load_graphml(self.graph_path)
                except (ParseError, ValueError, OSError):
                    self.graph_path.unlink(missing_ok=True)
                else:
                    if self._is_expected_network(cached_graph):
                        GraphService._shared_graph = cached_graph
                        GraphService._shared_graph_source = "cache"
                        return GraphService._shared_graph, GraphService._shared_graph_source

            try:
                graph = ox.graph_from_place(settings.osmnx_place_query, network_type=settings.osmnx_network_type, simplify=True)
                ox.save_graphml(graph, self.graph_path)
            except Exception as error:
                raise RuntimeError("No se pudo preparar el grafo de rutas.") from error

            GraphService._shared_graph = graph
            GraphService._shared_graph_source = "download"
            return GraphService._shared_graph, GraphService._shared_graph_source

    def _is_expected_network(self, graph: MultiDiGraph) -> bool:
        return graph.graph.get("network_type") == settings.osmnx_network_type
