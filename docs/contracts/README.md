# Contratos de integración frontend-backend

Estos contratos definen la interfaz de datos estable esperada por el frontend y expuesta por el backend de Brisa.

## Reglas
- Mantener nombres de campos estables antes de añadir nuevos consumidores.
- Indicar claramente campos obligatorios y opcionales.
- Actualizar este directorio antes de implementar cambios de integración.
- Cualquier cambio de contrato debe reflejarse también en `docs/slices/slice-X.md`.

## Relación feature -> contrato
- `api/health`: `health-response.contract.json`.
- `bicimad`: `stations.contract.json`.
- `search` + `routing`: `route-request.contract.json`, `route-response.contract.json`, `geocoding-suggest-response.contract.json`.
- `neighborhoods`: `neighborhood-score.contract.json`, `cyclability-neighborhoods.contract.json`.
- `safety`: `safety-grid-response.contract.json`, `safety-summary-response.contract.json`.
- Estado local de UI: `ui-state.contract.md`.
