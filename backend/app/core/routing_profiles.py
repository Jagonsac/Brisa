from dataclasses import dataclass
from os import getenv


@dataclass(frozen=True)
class RoutingProfilesConfig:
    cache_version: str = getenv("ROUTING_CACHE_VERSION", "v2")
    fastest_extreme_hostility_multiplier: float = float(getenv("FASTEST_EXTREME_HOSTILITY_MULTIPLIER", "0.5"))
    safe_risk_multiplier: float = float(getenv("SAFE_RISK_MULTIPLIER", "4.2"))
    balanced_risk_multiplier: float = float(getenv("BALANCED_RISK_MULTIPLIER", "2.1"))
    night_base_risk_multiplier: float = float(getenv("NIGHT_BASE_RISK_MULTIPLIER", "4.5"))
    night_lighting_multiplier: float = float(getenv("NIGHT_LIGHTING_MULTIPLIER", "2.4"))
    night_accident_multiplier: float = float(getenv("NIGHT_ACCIDENT_MULTIPLIER", "1.6"))
    night_start_hour: int = int(getenv("NIGHT_START_HOUR", "22"))
    night_end_hour: int = int(getenv("NIGHT_END_HOUR", "6"))


routing_profiles_config = RoutingProfilesConfig()
