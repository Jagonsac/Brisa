from dataclasses import dataclass
from os import getenv


@dataclass(frozen=True)
class RoutingProfilesConfig:
    cache_version: str = getenv("ROUTING_CACHE_VERSION", "v1")
    safe_risk_multiplier: float = float(getenv("SAFE_RISK_MULTIPLIER", "2.5"))
    balanced_risk_multiplier: float = float(getenv("BALANCED_RISK_MULTIPLIER", "1.1"))
    night_base_risk_multiplier: float = float(getenv("NIGHT_BASE_RISK_MULTIPLIER", "1.2"))
    night_lighting_multiplier: float = float(getenv("NIGHT_LIGHTING_MULTIPLIER", "1.0"))
    night_accident_multiplier: float = float(getenv("NIGHT_ACCIDENT_MULTIPLIER", "0.8"))
    night_start_hour: int = int(getenv("NIGHT_START_HOUR", "22"))
    night_end_hour: int = int(getenv("NIGHT_END_HOUR", "6"))
    lighting_csv_url: str = getenv(
        "LIGHTING_CSV_URL",
        "https://datos.madrid.es/dataset/300573-0-unidades-luminosas-farolas/resource/300573-0-unidades-luminosas-farolas-csv/download/300573-0-unidades-luminosas-farolas-csv.csv",
    )


routing_profiles_config = RoutingProfilesConfig()
