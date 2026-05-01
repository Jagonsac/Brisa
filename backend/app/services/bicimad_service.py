import asyncio
import json
from pathlib import Path
from typing import Literal

from app.clients.bicimad_client import BicimadClient
from app.core.config import settings
from app.schemas.station import StationsResponse
from app.utils.station_normalizer import normalize_gbfs_stations, normalize_geojson_stations, normalize_snapshot_stations

StationsSourceMode = Literal["auto", "remote", "snapshot"]


class BicimadService:
    def __init__(self, client: BicimadClient | None = None):
        self.client = client or BicimadClient()
        self.snapshot_path = Path(__file__).resolve().parent.parent / "data" / "bicimad_stations_snapshot.json"

    async def get_stations(self, source_mode: StationsSourceMode = "auto") -> StationsResponse:
        warnings: list[str] = []

        if source_mode in ("auto", "remote"):
            try:
                gbfs_payload = await self.client.fetch_json(settings.bicimad_stations_url)
                stations = normalize_gbfs_stations(gbfs_payload)
                if stations:
                    self._persist_snapshot(stations)
                    return StationsResponse(
                        data=stations,
                        meta={"count": len(stations), "source": "gbfs-station-information", "fallbackUsed": False, "warnings": warnings},
                    )
                warnings.append("GBFS no devolvió estaciones válidas.")
            except (Exception, asyncio.CancelledError) as error:
                warnings.append(f"GBFS falló: {error}")

            try:
                fallback_payload = await self.client.fetch_json(settings.bicimad_fallback_url)
                stations = normalize_geojson_stations(fallback_payload)
                if stations:
                    self._persist_snapshot(stations)
                    return StationsResponse(
                        data=stations,
                        meta={"count": len(stations), "source": "emt-geojson-fallback", "fallbackUsed": True, "warnings": warnings},
                    )
                warnings.append("Fallback GeoJSON no devolvió estaciones válidas.")
            except (Exception, asyncio.CancelledError) as error:
                warnings.append(f"GeoJSON oficial falló: {error}")

            if source_mode == "remote":
                raise RuntimeError(" | ".join(warnings) or "No fue posible cargar estaciones remotas.")

        snapshot_payload = self._load_snapshot()
        stations = normalize_snapshot_stations(snapshot_payload)
        if stations:
            return StationsResponse(
                data=stations,
                meta={"count": len(stations), "source": "local-snapshot-fallback", "fallbackUsed": True, "warnings": warnings},
            )

        raise RuntimeError(" | ".join(warnings) or "No fue posible cargar estaciones Bicimad.")

    def _load_snapshot(self) -> list[dict]:
        if not self.snapshot_path.exists():
            return []

        with self.snapshot_path.open("r", encoding="utf-8") as snapshot_file:
            return json.load(snapshot_file)

    def _persist_snapshot(self, stations: list[dict]) -> None:
        try:
            self.snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            self.snapshot_path.write_text(json.dumps(stations, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
