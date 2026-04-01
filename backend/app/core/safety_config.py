from dataclasses import dataclass
from os import getenv


@dataclass(frozen=True)
class SafetyWeights:
    accidents: float = float(getenv("SAFETY_WEIGHT_ACCIDENTS", "0.5"))
    traffic: float = float(getenv("SAFETY_WEIGHT_TRAFFIC", "0.2"))
    hostile_roads: float = float(getenv("SAFETY_WEIGHT_HOSTILE_ROADS", "0.2"))
    bike_infra: float = float(getenv("SAFETY_WEIGHT_BIKE_INFRA", "0.1"))


@dataclass(frozen=True)
class SafetyConfig:
    version: str = "v1"
    city_name: str = getenv("SAFETY_CITY_NAME", "Madrid")
    cell_size_meters: int = int(getenv("SAFETY_CELL_SIZE_METERS", "250"))
    source_crs: str = getenv("SAFETY_ACCIDENTS_SOURCE_CRS", "EPSG:25830")
    target_crs: str = getenv("SAFETY_TARGET_CRS", "EPSG:4326")
    projected_crs: str = getenv("SAFETY_PROJECTED_CRS", "EPSG:25830")
    accidents_csv_url: str = getenv(
        "SAFETY_ACCIDENTS_CSV_URL",
        "https://datos.madrid.es/dataset/300110-0-accidentes-bicicleta/resource/300110-0-accidentes-bicicleta-csv/download/300110-0-accidentes-bicicleta-csv.csv",
    )
    traffic_stations_csv_url: str = getenv(
        "SAFETY_TRAFFIC_STATIONS_CSV_URL",
        "https://datos.madrid.es/dataset/300233-0-aforo-trafico-permanentes/resource/300233-112-aforo-trafico-permanentes-csv/download/300233-112-aforo-trafico-permanentes-csv.csv",
    )
    traffic_monthly_api_url: str = getenv(
        "SAFETY_TRAFFIC_MONTHLY_API_URL",
        "https://datos.madrid.es/api/3/action/datastore_search?resource_id=300233-6-aforo-trafico-permanentes-xlsx&limit=50000",
    )
    traffic_influence_radius_meters: int = int(getenv("SAFETY_TRAFFIC_RADIUS_METERS", "450"))
    hostile_highway_classes: tuple[str, ...] = (
        "trunk",
        "primary",
        "secondary",
        "trunk_link",
        "primary_link",
        "secondary_link",
    )
    bike_friendly_highway_classes: tuple[str, ...] = ("cycleway", "residential", "living_street")
    download_timeout_seconds: int = int(getenv("SAFETY_DOWNLOAD_TIMEOUT_SECONDS", "40"))

    @property
    def weights(self) -> SafetyWeights:
        return SafetyWeights()


safety_config = SafetyConfig()
