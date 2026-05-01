from dataclasses import dataclass, field
from os import getenv


@dataclass(frozen=True)
class SafetyConfig:
    version: str = getenv("SAFETY_VERSION", "v2")
    source_crs: str = getenv("SAFETY_ACCIDENTS_SOURCE_CRS", "EPSG:25830")
    target_crs: str = getenv("SAFETY_TARGET_CRS", "EPSG:4326")
    projected_crs: str = getenv("SAFETY_PROJECTED_CRS", "EPSG:25830")
    cell_size_meters: int = int(getenv("SAFETY_CELL_SIZE_METERS", "250"))
    download_timeout_seconds: int = int(getenv("SAFETY_DOWNLOAD_TIMEOUT_SECONDS", "40"))

    accident_radius_m: float = float(getenv("SAFETY_ACCIDENT_RADIUS_M", "30"))
    traffic_radius_m: float = float(getenv("SAFETY_TRAFFIC_RADIUS_M", "50"))
    imd_radius_m: float = float(getenv("SAFETY_IMD_RADIUS_M", "65"))
    lighting_radius_m: float = float(getenv("SAFETY_LIGHTING_RADIUS_M", "35"))
    crossing_radius_m: float = float(getenv("SAFETY_CROSSING_RADIUS_M", "40"))
    bike_presence_radius_m: float = float(getenv("SAFETY_BIKE_PRESENCE_RADIUS_M", "45"))

    signal_scale_divisor: float = float(getenv("SAFETY_SIGNAL_SCALE_DIVISOR", "12"))
    accident_prior_mean: float = float(getenv("SAFETY_ACCIDENT_PRIOR_MEAN", "0.18"))
    accident_prior_strength: float = float(getenv("SAFETY_ACCIDENT_PRIOR_STRENGTH", "3.5"))

    day_weights: dict[str, float] = field(
        default_factory=lambda: {
            "road_hostility": float(getenv("SAFETY_DAY_W_ROAD_HOSTILITY", "0.30")),
            "traffic": float(getenv("SAFETY_DAY_W_TRAFFIC", "0.25")),
            "junction": float(getenv("SAFETY_DAY_W_JUNCTION", "0.12")),
            "accident_general": float(getenv("SAFETY_DAY_W_ACC_GENERAL", "0.20")),
            "accident_bike": float(getenv("SAFETY_DAY_W_ACC_BIKE", "0.08")),
            "bike_bonus": float(getenv("SAFETY_DAY_W_BIKE_BONUS", "0.16")),
        }
    )
    night_weights: dict[str, float] = field(
        default_factory=lambda: {
            "lighting": float(getenv("SAFETY_NIGHT_W_LIGHTING", "0.28")),
            "night_accidents": float(getenv("SAFETY_NIGHT_W_ACCIDENTS", "0.22")),
            "night_traffic": float(getenv("SAFETY_NIGHT_W_TRAFFIC", "0.20")),
            "junction": float(getenv("SAFETY_NIGHT_W_JUNCTION", "0.10")),
        }
    )

    highway_hostility: dict[str, float] = field(
        default_factory=lambda: {
            "cycleway": 0.08,
            "living_street": 0.12,
            "residential": 0.25,
            "service": 0.25,
            "unclassified": 0.3,
            "tertiary": 0.52,
            "tertiary_link": 0.58,
            "secondary": 0.72,
            "secondary_link": 0.78,
            "primary": 0.88,
            "primary_link": 0.90,
            "trunk": 0.98,
            "trunk_link": 0.99,
            "default": 0.45,
        }
    )

    general_accidents_csv_url: str = getenv(
        "GENERAL_ACCIDENTS_CSV_URL",
        "https://datos.madrid.es/dataset/300228-0-accidentes-trafico-detalle/resource/300228-34-accidentes-trafico-detalle/download/300228-34-accidentes-trafico-detalle.csv",
    )
    bike_accidents_csv_url: str = getenv(
        "BIKE_ACCIDENTS_CSV_URL",
        "https://datos.madrid.es/dataset/300110-0-accidentes-bicicleta/resource/300110-0-accidentes-bicicleta-csv/download/300110-0-accidentes-bicicleta-csv.csv",
    )
    traffic_non_permanent_csv_url: str = getenv(
        "TRAFFIC_NON_PERMANENT_CSV_URL",
        "https://datos.madrid.es/dataset/300209-0-aforos-no-permanentes/resource/300209-1-aforos-no-permanentes-csv/download/300209-1-aforos-no-permanentes-csv.csv",
    )
    imd_csv_url: str = getenv("IMD_CSV_URL", "https://datos.madrid.es/dataset/203962-0-trafico-imd")
    crossings_csv_url: str = getenv("CROSSINGS_CSV_URL", "https://datos.madrid.es/dataset/300275-0-cruces-semaforizados")
    bike_crossings_csv_url: str = getenv("BIKE_CROSSINGS_CSV_URL", "https://datos.madrid.es/dataset/205159-0-bici-cruces-semaforizados")
    lighting_csv_url: str = getenv(
        "LIGHTING_CSV_URL",
        "https://datos.madrid.es/dataset/300573-0-unidades-luminosas-farolas/resource/300573-0-unidades-luminosas-farolas-csv/download/300573-0-unidades-luminosas-farolas-csv.csv",
    )
    bike_counts_csv_url: str = getenv(
        "BIKE_COUNTS_CSV_URL",
        "https://datos.madrid.es/dataset/300321-0-aforos-peatones-bicicletas/resource/300321-10-aforos-peatones-bicicletas-csv/download/300321-10-aforos-peatones-bicicletas-csv.csv",
    )

    # Compatibilidad con servicios de slices anteriores
    accidents_csv_url: str = bike_accidents_csv_url
    traffic_stations_csv_url: str = getenv(
        "SAFETY_TRAFFIC_STATIONS_CSV_URL",
        "https://datos.madrid.es/dataset/300233-0-aforo-trafico-permanentes/resource/300233-112-aforo-trafico-permanentes-csv/download/300233-112-aforo-trafico-permanentes-csv.csv",
    )
    traffic_monthly_api_url: str = getenv(
        "SAFETY_TRAFFIC_MONTHLY_API_URL",
        "https://datos.madrid.es/api/3/action/datastore_search?resource_id=300233-6-aforo-trafico-permanentes-xlsx&limit=50000",
    )
    neighborhoods_geojson_url: str = getenv(
        "SAFETY_NEIGHBORHOODS_GEOJSON_URL",
        "https://sigma.madrid.es/hosted/rest/services/CARTOGRAFIA/LIMITES_ADMINISTRATIVOS/MapServer/25/query?where=1%3D1&outFields=COD_BAR%2CNOMBRE%2CNOMDIS&outSR=4326&f=geojson",
    )
    neighborhoods_geojson_fallback_urls: tuple[str, ...] = (
        "https://datos.madrid.es/egob/catalogo/212070-0-barrios.geojson",
        "https://datos.madrid.es/egob/catalogo/200078-1-barrios.geojson",
    )
    neighborhoods_cache_filename: str = getenv("SAFETY_NEIGHBORHOODS_CACHE_FILENAME", "madrid_barrios.geojson")
    traffic_influence_radius_meters: int = int(getenv("SAFETY_TRAFFIC_RADIUS_METERS", "450"))
    hostile_highway_classes: tuple[str, ...] = ("trunk", "primary", "secondary", "trunk_link", "primary_link", "secondary_link")
    bike_friendly_highway_classes: tuple[str, ...] = ("cycleway", "residential", "living_street")

    @dataclass(frozen=True)
    class GridWeights:
        accidents: float
        traffic: float
        hostile_roads: float
        bike_infra: float

    weights: GridWeights = field(
        default_factory=lambda: SafetyConfig.GridWeights(
            accidents=float(getenv("SAFETY_GRID_W_ACCIDENTS", "0.40")),
            traffic=float(getenv("SAFETY_GRID_W_TRAFFIC", "0.25")),
            hostile_roads=float(getenv("SAFETY_GRID_W_HOSTILE_ROADS", "0.25")),
            bike_infra=float(getenv("SAFETY_GRID_W_BIKE_INFRA", "0.20")),
        )
    )


safety_config = SafetyConfig()
