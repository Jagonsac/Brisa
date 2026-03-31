from dataclasses import dataclass

from app.clients.bicimad_client import BicimadClient
from app.core.config import settings


@dataclass(frozen=True)
class GeocodedPoint:
    query: str
    display_name: str
    lat: float
    lon: float


class GeocodingService:
    def __init__(self, client: BicimadClient | None = None) -> None:
        self.client = client or BicimadClient(timeout=12.0)

    async def geocode(self, query: str) -> GeocodedPoint:
        enriched_query = self._to_madrid_query(query)
        payload = await self.client.fetch_json(
            settings.nominatim_base_url,
            params={
                "format": "jsonv2",
                "q": enriched_query,
                "limit": 1,
                "countrycodes": settings.nominatim_country_codes,
                "addressdetails": 1,
            },
            headers={"User-Agent": settings.nominatim_user_agent},
        )
        if not isinstance(payload, list) or len(payload) == 0:
            raise ValueError(f"No encontramos resultados para '{query}'.")

        result = payload[0]
        lat = result.get("lat")
        lon = result.get("lon")
        display_name = result.get("display_name")
        if lat is None or lon is None or display_name is None:
            raise RuntimeError("Respuesta de geocodificación inválida.")

        return GeocodedPoint(query=query, display_name=display_name, lat=float(lat), lon=float(lon))

    @staticmethod
    def _to_madrid_query(query: str) -> str:
        if "madrid" in query.lower():
            return query
        return f"{query}, Madrid, Spain"
