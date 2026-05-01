from dataclasses import dataclass, field
from os import getenv


@dataclass(frozen=True)
class CyclabilityConfig:
    version: str = getenv("CYCLABILITY_VERSION", "v1")
    assigned_edge_buffer_m: float = float(getenv("CYCLABILITY_ASSIGNED_EDGE_BUFFER_M", "35"))
    bicimad_coverage_buffer_m: float = float(getenv("CYCLABILITY_BICIMAD_BUFFER_M", "400"))
    robust_p_low: float = float(getenv("CYCLABILITY_ROBUST_P_LOW", "0.05"))
    robust_p_high: float = float(getenv("CYCLABILITY_ROBUST_P_HIGH", "0.95"))
    park_rebalance_enabled: bool = getenv("CYCLABILITY_PARK_REBALANCE_ENABLED", "1") not in {"0", "false", "False"}
    park_green_share_threshold: float = float(getenv("CYCLABILITY_PARK_GREEN_SHARE_THRESHOLD", "0.45"))
    park_hostile_share_max: float = float(getenv("CYCLABILITY_PARK_HOSTILE_SHARE_MAX", "0.20"))
    park_network_km_min: float = float(getenv("CYCLABILITY_PARK_NETWORK_KM_MIN", "15.0"))
    park_bike_accident_relative_max: float = float(getenv("CYCLABILITY_PARK_BIKE_ACCIDENT_RELATIVE_MAX", "0.85"))
    park_green_score_threshold: float = float(getenv("CYCLABILITY_PARK_GREEN_SCORE_THRESHOLD", "60.0"))
    park_hostility_score_threshold: float = float(getenv("CYCLABILITY_PARK_HOSTILITY_SCORE_THRESHOLD", "55.0"))
    park_safety_score_threshold: float = float(getenv("CYCLABILITY_PARK_SAFETY_SCORE_THRESHOLD", "50.0"))
    park_floor_base: float = float(getenv("CYCLABILITY_PARK_FLOOR_BASE", "60.0"))
    park_floor_high: float = float(getenv("CYCLABILITY_PARK_FLOOR_HIGH", "70.0"))
    park_floor_high_trigger: float = float(getenv("CYCLABILITY_PARK_FLOOR_HIGH_TRIGGER", "0.72"))

    weights: dict[str, float] = field(
        default_factory=lambda: {
            "safety": float(getenv("CYCLABILITY_W_SAFETY", "40")),
            "bike_infra": float(getenv("CYCLABILITY_W_BIKE_INFRA", "18")),
            "low_hostility": float(getenv("CYCLABILITY_W_LOW_HOSTILITY", "14")),
            "green_cyclable": float(getenv("CYCLABILITY_W_GREEN_CYCLABLE", "10")),
            "night": float(getenv("CYCLABILITY_W_NIGHT", "9")),
            "junction": float(getenv("CYCLABILITY_W_JUNCTION", "5")),
            "bicimad": float(getenv("CYCLABILITY_W_BICIMAD", "4")),
        }
    )
    park_weights: dict[str, float] = field(
        default_factory=lambda: {
            "safety": float(getenv("CYCLABILITY_PARK_W_SAFETY", "28")),
            "bike_infra": float(getenv("CYCLABILITY_PARK_W_BIKE_INFRA", "10")),
            "low_hostility": float(getenv("CYCLABILITY_PARK_W_LOW_HOSTILITY", "22")),
            "green_cyclable": float(getenv("CYCLABILITY_PARK_W_GREEN_CYCLABLE", "24")),
            "night": float(getenv("CYCLABILITY_PARK_W_NIGHT", "10")),
            "junction": float(getenv("CYCLABILITY_PARK_W_JUNCTION", "4")),
            "bicimad": float(getenv("CYCLABILITY_PARK_W_BICIMAD", "2")),
        }
    )


cyclability_config = CyclabilityConfig()
