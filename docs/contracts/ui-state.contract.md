# UI State Contract (frontend)

Estado mínimo esperado para la shell de Brisa:

- `origin` (string, obligatorio)
- `destination` (string, obligatorio)
- `selected_mode` (enum: `fast`, `safe`, `balanced`, `night`, obligatorio)
- `route_preparation_status` (enum: `idle`, `ready`, `error`, obligatorio)
- `message` (string, opcional)

Este contrato sirve para mantener consistencia de estado entre componentes de búsqueda y panel de mapa.
