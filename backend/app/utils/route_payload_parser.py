from dataclasses import dataclass
from typing import Any


class RoutePayloadError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class NormalizedRoutePoint:
    query: str
    lat: float | None
    lon: float | None


@dataclass(frozen=True)
class NormalizedRoutePayload:
    origin: NormalizedRoutePoint
    destination: NormalizedRoutePoint
    mode: str
    use_bicimad: bool


_ALLOWED_MODES = {"fastest", "safe", "balanced", "night"}


def parse_route_payload(payload: dict[str, Any]) -> NormalizedRoutePayload:
    if not isinstance(payload, dict):
        raise RoutePayloadError("El cuerpo de la petición debe ser un objeto JSON.")

    mode = _parse_mode(payload.get("mode"))
    origin = _parse_point(payload, point_key="origin", query_key="originQuery", point_label="origen")
    destination = _parse_point(payload, point_key="destination", query_key="destinationQuery", point_label="destino")

    use_bicimad = _parse_use_bicimad(payload)
    return NormalizedRoutePayload(origin=origin, destination=destination, mode=mode, use_bicimad=use_bicimad)


def _parse_mode(raw_mode: Any) -> str:
    if raw_mode is None:
        raise RoutePayloadError("Falta el modo de ruta. Usa mode='fastest'.")

    mode = str(raw_mode).strip().lower()
    if mode not in _ALLOWED_MODES:
        valid_modes = ", ".join(sorted(_ALLOWED_MODES))
        raise RoutePayloadError(f"El modo '{mode or raw_mode}' no es válido. Modos permitidos: {valid_modes}.")

    return mode


def _parse_use_bicimad(payload: dict[str, Any]) -> bool:
    if "useBicimad" in payload:
        return bool(payload.get("useBicimad"))

    transport_mode = str(payload.get("transportMode", "")).strip().lower()
    return transport_mode == "bicimad"


def _parse_point(payload: dict[str, Any], *, point_key: str, query_key: str, point_label: str) -> NormalizedRoutePoint:
    point_data = payload.get(point_key)
    point_dict = point_data if isinstance(point_data, dict) else {}

    query = _clean_query(point_dict.get("query"))
    if query == "":
        query = _clean_query(payload.get(query_key))

    lat_raw = point_dict.get("lat", point_dict.get("latitude"))
    lon_raw = point_dict.get("lon", point_dict.get("lng", point_dict.get("longitude")))

    lat = _coerce_float(lat_raw, field_name=f"{point_key}.lat")
    lon = _coerce_float(lon_raw, field_name=f"{point_key}.lon")

    if (lat is None) != (lon is None):
        raise RoutePayloadError(f"{point_label.title()}: lat y lon deben enviarse juntos.")

    if query == "" and (lat is None or lon is None):
        raise RoutePayloadError(
            f"Faltan datos para el {point_label}. Envía query o lat/lon completos."
        )

    return NormalizedRoutePoint(query=query, lat=lat, lon=lon)


def _clean_query(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _coerce_float(value: Any, *, field_name: str) -> float | None:
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None

    try:
        return float(value)
    except (TypeError, ValueError) as error:
        raise RoutePayloadError(f"El campo {field_name} debe ser numérico.") from error
