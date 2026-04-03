from dataclasses import dataclass, field
from os import getenv


@dataclass(frozen=True)
class CyclabilityConfig:
    version: str = getenv("CYCLABILITY_VERSION", "v1")
    assigned_edge_buffer_m: float = float(getenv("CYCLABILITY_ASSIGNED_EDGE_BUFFER_M", "35"))
    bicimad_coverage_buffer_m: float = float(getenv("CYCLABILITY_BICIMAD_BUFFER_M", "400"))
    robust_p_low: float = float(getenv("CYCLABILITY_ROBUST_P_LOW", "0.10"))
    robust_p_high: float = float(getenv("CYCLABILITY_ROBUST_P_HIGH", "0.90"))

    weights: dict[str, float] = field(
        default_factory=lambda: {
            "safety": float(getenv("CYCLABILITY_W_SAFETY", "28")),
            "bike_infra": float(getenv("CYCLABILITY_W_BIKE_INFRA", "20")),
            "low_hostility": float(getenv("CYCLABILITY_W_LOW_HOSTILITY", "16")),
            "green_cyclable": float(getenv("CYCLABILITY_W_GREEN_CYCLABLE", "12")),
            "night": float(getenv("CYCLABILITY_W_NIGHT", "12")),
            "junction": float(getenv("CYCLABILITY_W_JUNCTION", "8")),
            "bicimad": float(getenv("CYCLABILITY_W_BICIMAD", "4")),
        }
    )


cyclability_config = CyclabilityConfig()
