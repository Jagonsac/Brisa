# Neighborhood cyclability

Services/hooks load rankings, GeoJSON, neighborhood detail, score breakdowns, and comparisons. The map layer is mounted in the main app. `NeighborhoodCyclabilityPanel` contains ranking/detail/comparison UI, but the current `AppLayout` does not mount that standalone panel.

Scoring remains in the backend. See the [model](../../../docs/routing-model.md#8-separate-map-and-neighborhood-models) and [limitations](../../../docs/known-issues.md).
