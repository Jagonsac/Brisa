from pathlib import Path

import osmnx as ox
from networkx import MultiDiGraph

from app.core.config import settings


class GraphService:
    def __init__(self) -> None:
        self._graph: MultiDiGraph | None = None
        self._graph_source: str = "cache"
        self.graphs_dir = Path(__file__).resolve().parents[2] / "data" / "graphs"
        self.graph_path = self.graphs_dir / settings.osmnx_graph_filename

    def get_graph(self) -> tuple[MultiDiGraph, str]:
        if self._graph is not None:
            return self._graph, self._graph_source

        self.graphs_dir.mkdir(parents=True, exist_ok=True)
        if self.graph_path.exists():
            self._graph = ox.load_graphml(self.graph_path)
            self._graph_source = "cache"
            return self._graph, self._graph_source

        try:
            graph = ox.graph_from_place(settings.osmnx_place_query, network_type=settings.osmnx_network_type, simplify=True)
            ox.save_graphml(graph, self.graph_path)
        except Exception as error:
            raise RuntimeError("No se pudo preparar el grafo de rutas.") from error

        self._graph = graph
        self._graph_source = "download"
        return self._graph, self._graph_source
