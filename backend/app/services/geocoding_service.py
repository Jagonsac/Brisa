from dataclasses import dataclass

from app.clients.bicimad_client import BicimadClient
from app.core.config import settings


class GeocodingError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class GeocodedPoint:
    query: str
    display_name: str
    lat: float
    lon: float


class GeocodingService:
    def __init__(self, client: BicimadClient | None = None) -> None:
        self.client = client or BicimadClient(timeout=12.0)

    async def geocode(self, query: str, *, point_label: str = "punto") -> GeocodedPoint:
        clean_query = query.strip()
        if len(clean_query) < 2:
            raise GeocodingError("invalid_query", f"El {point_label} debe tener al menos 2 caracteres.")

        payload = await self._search_nominatim(clean_query, limit=1)
        if not isinstance(payload, list) or len(payload) == 0:
            raise GeocodingError("location_not_found", f"No hemos podido localizar el {point_label} indicado.")

        result = payload[0]
        lat = result.get("lat")
        lon = result.get("lon")
        display_name = result.get("display_name")
        if lat is None or lon is None or display_name is None:
            raise GeocodingError("invalid_provider_payload", "La geocodificación devolvió una respuesta incompleta.")

        return GeocodedPoint(query=clean_query, display_name=display_name, lat=float(lat), lon=float(lon))

    async def suggest(self, query: str) -> list[dict]:
        clean_query = query.strip()
        if len(clean_query) < 3:
            return []

        payload = await self._search_nominatim(clean_query, limit=5)
        if not isinstance(payload, list):
            raise GeocodingError("invalid_provider_payload", "No hemos podido obtener sugerencias en este momento.")

        suggestions: list[dict] = []
        for item in payload:
            lat = item.get("lat")
            lon = item.get("lon")
            label = item.get("display_name")
            if lat is None or lon is None or label is None:
                continue

            name_hint = item.get("name") or clean_query
            suggestions.append(
                {
                    "label": str(label),
                    "value": str(name_hint),
                    "lat": float(lat),
                    "lon": float(lon),
                }
            )

        return suggestions

    async def _search_nominatim(self, query: str, *, limit: int) -> list[dict]:
        enriched_query = self._to_madrid_query(query)
        params = {
            "format": "jsonv2",
            "q": enriched_query,
            "limit": limit,
            "countrycodes": settings.nominatim_country_codes,
            "addressdetails": 1,
            "dedupe": 1,
        }

        payload = await self.client.fetch_json(
            settings.nominatim_base_url,
            params=params,
            headers={"User-Agent": settings.nominatim_user_agent},
        )
        return payload

    @staticmethod
    def _to_madrid_query(query: str) -> str:
        if "madrid" in query.lower():
            return query
        return f"{query}, Madrid, Spain"
