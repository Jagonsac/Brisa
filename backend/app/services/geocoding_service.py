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

        payload = await self._search_nominatim(clean_query, limit=5, dedupe=0)
        if not isinstance(payload, list):
            raise GeocodingError("invalid_provider_payload", "No hemos podido obtener sugerencias en este momento.")

        suggestions: list[dict] = []
        for item in payload:
            lat = item.get("lat")
            lon = item.get("lon")
            label = item.get("display_name")
            if lat is None or lon is None or label is None:
                continue

            display_text = self._build_display_text(item)
            if display_text == "":
                continue

            suggestions.append(
                {
                    "label": str(label),
                    "value": display_text,
                    "displayText": display_text,
                    "lat": float(lat),
                    "lon": float(lon),
                }
            )

        return suggestions

    async def _search_nominatim(self, query: str, *, limit: int, dedupe: int = 1) -> list[dict]:
        enriched_query = self._to_madrid_query(query)
        params = {
            "format": "jsonv2",
            "q": enriched_query,
            "limit": limit,
            "countrycodes": settings.nominatim_country_codes,
            "addressdetails": 1,
            "dedupe": dedupe,
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

    @staticmethod
    def _build_display_text(item: dict) -> str:
        address = item.get("address") if isinstance(item.get("address"), dict) else {}

        road = (
            address.get("road")
            or address.get("pedestrian")
            or address.get("street")
            or address.get("avenue")
            or address.get("cycleway")
            or address.get("living_street")
            or address.get("footway")
            or address.get("residential")
            or address.get("path")
            or address.get("square")
        )
        house_number = address.get("house_number") or address.get("housenumber")

        if road and house_number:
            return f"{road}, {house_number}".strip()

        if road:
            return str(road).strip()

        if house_number:
            label = item.get("display_name")
            if label:
                parts = [segment.strip() for segment in str(label).split(",") if segment.strip()]
                if len(parts) >= 2:
                    first_part = parts[0]
                    second_part = parts[1]
                    clean_house_number = str(house_number).strip()
                    if first_part == clean_house_number:
                        return f"{second_part}, {clean_house_number}".strip()
                    if second_part == clean_house_number and len(parts) >= 3:
                        return f"{parts[0]}, {clean_house_number}".strip()

        label = item.get("display_name")
        if label:
            parts = [segment.strip() for segment in str(label).split(",") if segment.strip()]
            if len(parts) >= 2:
                if any(char.isdigit() for char in parts[0]):
                    return parts[0]
                if any(char.isdigit() for char in parts[1]):
                    return f"{parts[0]}, {parts[1]}"
            if parts:
                return parts[0]

        name = item.get("name")
        if name:
            return str(name).strip()

        return ""
