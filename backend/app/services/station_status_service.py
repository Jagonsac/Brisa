import threading
import time
from typing import Any

from app.clients.bicimad_client import BicimadClient
from app.core.config import settings


class StationStatusService:
    _cache: dict[str, dict[str, Any]] = {}
    _cached_at: float = 0.0
    _lock = threading.Lock()

    def __init__(self, client: BicimadClient | None = None) -> None:
        self.client = client or BicimadClient()

    async def get_status(self) -> tuple[dict[str, dict[str, Any]], bool]:
        now = time.time()
        if StationStatusService._cache and (now - StationStatusService._cached_at) <= settings.bicimad_status_ttl_seconds:
            return StationStatusService._cache, True

        with StationStatusService._lock:
            if StationStatusService._cache and (now - StationStatusService._cached_at) <= settings.bicimad_status_ttl_seconds:
                return StationStatusService._cache, True

        payload = await self.client.fetch_json(settings.bicimad_status_url)
        normalized = self._normalize(payload)

        with StationStatusService._lock:
            StationStatusService._cache = normalized
            StationStatusService._cached_at = time.time()

        return normalized, False

    def get_cached_status(self) -> dict[str, dict[str, Any]]:
        return StationStatusService._cache

    @staticmethod
    def _normalize(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
        stations = payload.get("data", {}).get("stations", [])
        if not isinstance(stations, list):
            return {}

        normalized: dict[str, dict[str, Any]] = {}
        for station in stations:
            station_id = str(station.get("station_id") or "").strip()
            if station_id == "":
                continue

            bikes_available = StationStatusService._to_int(
                station.get("num_bikes_available")
                or station.get("num_bikes_available_types", {}).get("mechanical")
                or station.get("num_bikes_available_types", {}).get("ebike")
            )
            docks_available = StationStatusService._to_int(station.get("num_docks_available"))
            normalized[station_id] = {
                "bikesAvailable": bikes_available,
                "docksAvailable": docks_available,
                "isRenting": bool(station.get("is_renting", True)),
                "isReturning": bool(station.get("is_returning", True)),
                "isInstalled": bool(station.get("is_installed", True)),
            }

        return normalized

    @staticmethod
    def _to_int(value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
