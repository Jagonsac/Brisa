# BiciMAD integration

Services load normalized station locations from the API, then direct providers or a local snapshot when needed. Utilities normalize provider shapes; hooks manage loading/error state; components render station markers and multimodal information.

The current planner selects stations by proximity. Live bike/dock availability is not used for route selection, despite status-related feature flags and legacy UI text. See the [known issues](../../../docs/known-issues.md#bicimad-selection-and-explanation-disagree).
