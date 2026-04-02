from __future__ import annotations

from dataclasses import dataclass


NON_CYCLABLE_HIGHWAYS = {"motorway", "motorway_link"}
HOSTILE_DEFAULT_HIGHWAYS = {"trunk", "trunk_link"}
PROTECTED_CYCLEWAY_VALUES = {"track", "separate", "opposite_track", "crossing"}


@dataclass(frozen=True)
class BikeLegalityDecision:
    allowed: bool
    reason: str


def _as_tokens(value) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, list):
        out: set[str] = set()
        for item in value:
            out.update(_as_tokens(item))
        return out
    return {token.strip().lower() for token in str(value).replace(";", ",").split(",") if token.strip()}


def _is_no(value) -> bool:
    tokens = _as_tokens(value)
    return "no" in tokens or "private" in tokens


def _has_explicit_bike_infra(edge: dict) -> bool:
    cycleway_tokens = set()
    for key in ("cycleway", "cycleway:left", "cycleway:right", "cycleway:both"):
        cycleway_tokens.update(_as_tokens(edge.get(key)))

    bicycle_tokens = _as_tokens(edge.get("bicycle"))
    highway_tokens = _as_tokens(edge.get("highway"))
    segregated_tokens = _as_tokens(edge.get("segregated"))

    if "cycleway" in highway_tokens:
        return True
    if cycleway_tokens & PROTECTED_CYCLEWAY_VALUES:
        return True
    if "designated" in bicycle_tokens and ("yes" in segregated_tokens or cycleway_tokens):
        return True
    return False


def evaluate_bike_legality(edge: dict) -> BikeLegalityDecision:
    highway_tokens = _as_tokens(edge.get("highway"))
    if highway_tokens & NON_CYCLABLE_HIGHWAYS:
        return BikeLegalityDecision(False, "highway_non_cyclable")

    if _is_no(edge.get("motorroad")) is False and "yes" in _as_tokens(edge.get("motorroad")):
        return BikeLegalityDecision(False, "motorroad")

    bicycle_tokens = _as_tokens(edge.get("bicycle"))
    access_tokens = _as_tokens(edge.get("access"))

    if "no" in bicycle_tokens:
        return BikeLegalityDecision(False, "bicycle_no")
    if "no" in access_tokens and not ({"yes", "designated"} & bicycle_tokens):
        return BikeLegalityDecision(False, "access_no")

    if highway_tokens & HOSTILE_DEFAULT_HIGHWAYS and not _has_explicit_bike_infra(edge):
        return BikeLegalityDecision(False, "trunk_without_bike_infra")

    return BikeLegalityDecision(True, "allowed")


def osm_bike_infra_score(edge: dict) -> float:
    score = 0.0
    cycleway_tokens = set()
    for key in ("cycleway", "cycleway:left", "cycleway:right", "cycleway:both"):
        cycleway_tokens.update(_as_tokens(edge.get(key)))

    if "highway" in edge and "cycleway" in _as_tokens(edge.get("highway")):
        return 1.0

    if cycleway_tokens & {"track", "separate", "opposite_track"}:
        score = max(score, 0.9)
    elif cycleway_tokens & {"lane", "opposite_lane", "shared_lane"}:
        score = max(score, 0.55)
    elif cycleway_tokens:
        score = max(score, 0.35)

    if "designated" in _as_tokens(edge.get("bicycle")):
        score = max(score, 0.45)
    if "yes" in _as_tokens(edge.get("segregated")):
        score = min(1.0, score + 0.15)

    return float(max(0.0, min(1.0, score)))
