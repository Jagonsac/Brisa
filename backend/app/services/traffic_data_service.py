import csv
import io
import json
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen

from app.core.safety_config import safety_config


@dataclass
class TrafficStation:
    station_id: str
    lat: float
    lon: float
    intensity: float


class TrafficDataService:
    def __init__(self) -> None:
        self.raw_dir = Path(__file__).resolve().parents[2] / "data" / "safety" / "raw"

    def load_traffic_stations(self) -> tuple[list[TrafficStation], dict]:
        station_rows = self._download_csv_rows(safety_config.traffic_stations_csv_url, "aforos_permanentes_estaciones.csv")
        intensity_by_station, monthly_meta = self._load_monthly_intensity()

        stations: list[TrafficStation] = []
        for row in station_rows:
            station_id = str(row.get("Estacion") or row.get("estacion") or row.get("id") or "").strip()
            lat = self._parse_float(row.get("Latitud") or row.get("latitud") or row.get("Y"))
            lon = self._parse_float(row.get("Longitud") or row.get("longitud") or row.get("X"))
            if not station_id or lat is None or lon is None:
                continue

            intensity = intensity_by_station.get(station_id, 1.0)
            stations.append(TrafficStation(station_id=station_id, lat=lat, lon=lon, intensity=float(intensity)))

        fallback_used = monthly_meta.get("fallbackUsed", True)
        meta = {
            "recordsDownloaded": len(station_rows),
            "recordsUsed": len(stations),
            "trafficFallbackUsed": fallback_used,
            "monthlyDataset": monthly_meta,
        }
        return stations, meta

    def _load_monthly_intensity(self) -> tuple[dict[str, float], dict]:
        output = self.raw_dir / "aforos_permanentes_mensual.json"
        request = Request(
            safety_config.traffic_monthly_api_url,
            headers={"User-Agent": "Brisa/0.1 (safety slice 5)"},
        )
        try:
            with urlopen(request, timeout=safety_config.download_timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8", errors="ignore"))
            output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            records = payload.get("result", {}).get("records", [])
        except Exception as error:
            return {}, {"fallbackUsed": True, "reason": f"No se pudo usar API mensual: {error}"}

        intensity_by_station: dict[str, list[float]] = {}
        selected_field = None

        for record in records:
            station_id = str(record.get("Estacion") or record.get("ESTACION") or record.get("id") or "").strip()
            if not station_id:
                continue

            if selected_field is None:
                selected_field = self._find_intensity_field(record)
            if selected_field is None:
                continue

            intensity = self._parse_float(record.get(selected_field))
            if intensity is None:
                continue
            intensity_by_station.setdefault(station_id, []).append(intensity)

        averaged = {station: sum(values) / len(values) for station, values in intensity_by_station.items() if values}
        if not averaged:
            return {}, {
                "fallbackUsed": True,
                "reason": "No se encontró campo robusto de intensidad en dataset mensual.",
            }

        return averaged, {
            "fallbackUsed": False,
            "records": len(records),
            "stationMatches": len(averaged),
            "selectedField": selected_field,
        }

    def _download_csv_rows(self, url: str, filename: str) -> list[dict]:
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        request = Request(url, headers={"User-Agent": "Brisa/0.1 (safety slice 5)"})
        with urlopen(request, timeout=safety_config.download_timeout_seconds) as response:
            raw_bytes = response.read()

        (self.raw_dir / filename).write_bytes(raw_bytes)
        text = raw_bytes.decode("utf-8-sig", errors="ignore")
        sample = "\n".join(text.splitlines()[:6])
        delimiter = ";" if sample.count(";") >= sample.count(",") else ","
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        return list(reader)

    @staticmethod
    def _find_intensity_field(record: dict) -> str | None:
        candidates = []
        for key in record.keys():
            lower = key.lower()
            if "intens" in lower or "volumen" in lower or "conteo" in lower:
                candidates.append(key)
        return candidates[0] if candidates else None

    @staticmethod
    def _parse_float(value) -> float | None:
        if value is None:
            return None
        if isinstance(value, (float, int)):
            return float(value)
        cleaned = str(value).replace(".", "").replace(",", ".").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None
