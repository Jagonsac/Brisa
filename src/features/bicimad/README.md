# Feature: bicimad

Integración de estaciones Bicimad para Slice 2 con arquitectura modular.

## Estructura
- `services/`: acceso a fuentes remotas y estrategia de fallback.
- `utils/`: normalización a contrato interno estable.
- `hooks/`: estado de carga para UI (`useBicimadStations`).
- `components/`: capa visual de mapa + estado de integración.

## Alcance actual (Slice 2)
- Carga de estaciones desde `station_information` (GBFS).
- Fallback oficial EMT GeoJSON.
- Fallback local para demo estable.
- Render de estaciones en mapa con popup mínimo.

## Preparado para siguiente slice
- Incorporar `station_status` sin romper el contrato de UI.
