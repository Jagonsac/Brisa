# Contratos de integración frontend-backend

Este directorio define la interfaz de datos pública y estable usada por Brisa entre frontend y backend.

## Objetivo

- Evitar acoplamiento a payloads crudos de proveedores externos.
- Permitir evolución interna del backend sin romper la UI.
- Centralizar validación y versionado de campos.

## Reglas

- Mantener nombres y estructura de campos estables.
- Documentar explícitamente campos obligatorios/opcionales.
- Actualizar contratos en el mismo cambio que modifique respuestas/requests.
- Reflejar cambios relevantes también en `README.md` y documentación técnica.

## Índice

- Salud: `health-response.contract.json`
- Estaciones Bicimad: `stations.contract.json` + `stations.mapping.md`
- Geocoding: `geocoding-suggest-response.contract.json`
- Routing: `route-request.contract.json`, `route-response.contract.json`
- Safety: `safety-grid-response.contract.json`, `safety-summary-response.contract.json`
- Ciclabilidad barrios: `cyclability-neighborhoods.contract.json`, `neighborhood-score.contract.json`
- Debug de score por barrio (temporal): `cyclability-score-breakdown.contract.json`
- Estado de UI: `ui-state.contract.md`
