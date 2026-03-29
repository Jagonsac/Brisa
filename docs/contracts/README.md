# Contratos de integración frontend-backend

Estos contratos definen la interfaz de datos esperada por el frontend de Brisa.

## Reglas
- Mantener nombres de campos estables y en `snake_case` para payloads de backend.
- Indicar claramente campos obligatorios y opcionales.
- Actualizar este directorio antes de implementar integraciones reales.

## Relación feature -> contrato
- `search` + `routing`: `route-request.contract.json`, `route-response.contract.json`.
- `bicimad`: `stations.contract.json`.
- `neighborhoods`: `neighborhood-score.contract.json`.
- Estado local de UI: `ui-state.contract.md`.
