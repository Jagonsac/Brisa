import csv
import io
import json
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen

from pyproj import Transformer

from app.core.safety_config import safety_config


@dataclass
class AccidentPoint:
    lat: float
    lon: float
    x: float
    y: float
    count: int
    weighted_score: float


class AccidentDataService:
    def __init__(self) -> None:
        self._to_wgs84 = Transformer.from_crs(safety_config.source_crs, safety_config.target_crs, always_xy=True)
        self._to_projected = Transformer.from_crs(safety_config.target_crs, safety_config.projected_crs, always_xy=True)
        self.raw_dir = Path(__file__).resolve().parents[2] / "data" / "safety" / "raw"

    def load_accidents(self) -> tuple[list[AccidentPoint], dict]:
        rows = self.load_raw_rows()
        deduped: dict[str, dict] = {}

        for row in rows:
            x = self.parse_float(row.get("coordenada_x_utm"))
            y = self.parse_float(row.get("coordenada_y_utm"))
            if x is None or y is None:
                continue

            lon, lat = self._to_wgs84.transform(x, y)
            if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                continue

            px, py = self._to_projected.transform(lon, lat)
            severity_weight = self.severity_weight(row)
            key = self._accident_key(row, x, y)
            previous = deduped.get(key)
            if previous is None:
                deduped[key] = {
                    "lat": lat,
                    "lon": lon,
                    "x": px,
                    "y": py,
                    "count": 1,
                    "weighted_score": severity_weight,
                }
                continue

            previous["weighted_score"] = max(previous["weighted_score"], severity_weight)

        points = [AccidentPoint(**item) for item in deduped.values()]
        meta = {
            "recordsDownloaded": len(rows),
            "recordsUsed": len(points),
            "deduplication": "Agrupación por num_expediente + fecha + hora + coordenadas UTM; se conserva severidad máxima.",
            "sourceCrs": safety_config.source_crs,
        }
        return points, meta

    def load_raw_rows(self) -> list[dict]:
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.raw_dir / "accidentes_bici_2024.csv"

        request = Request(
            safety_config.accidents_csv_url,
            headers={"User-Agent": "Brisa/0.1 (safety slice 5)"},
        )
        with urlopen(request, timeout=safety_config.download_timeout_seconds) as response:
            raw_bytes = response.read()

        output_path.write_bytes(raw_bytes)

        text = raw_bytes.decode("utf-8-sig", errors="ignore")
        sample = "\n".join(text.splitlines()[:6])
        delimiter = ";" if sample.count(";") >= sample.count(",") else ","
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        return list(reader)

    def severity_weight(self, row: dict) -> float:
        code = row.get("cod_lesividad")
        code_number = None
        if isinstance(code, str):
            digits = "".join(ch for ch in code if ch.isdigit())
            if digits:
                code_number = int(digits)
        if code_number is None:
            return 0.6
        if code_number <= 3:
            return 1.0
        if code_number <= 7:
            return 0.75
        return 0.45

    def _accident_key(self, row: dict, x: float, y: float) -> str:
        key = {
            "num_expediente": row.get("num_expediente", ""),
            "fecha": row.get("fecha", ""),
            "hora": row.get("hora", ""),
            "x": round(x, 1),
            "y": round(y, 1),
        }
        return json.dumps(key, sort_keys=True)

    @staticmethod
    def parse_float(value: str | None) -> float | None:
        if value is None:
            return None
        cleaned = value.replace(".", "").replace(",", ".").strip()
        if cleaned.count(".") > 1:
            parts = cleaned.split(".")
            cleaned = "".join(parts[:-1]) + "." + parts[-1]
        try:
            return float(cleaned)
        except ValueError:
            return None

    @property
    def to_wgs84(self) -> Transformer:
        return self._to_wgs84
