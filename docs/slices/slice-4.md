# Slice 4 — Routing real corregido y pulido (FastAPI + OSMnx)

## Problemas detectados
- Error opaco `Failed to fetch` al calcular rutas (sin mensaje útil para usuario).
- Conectividad frontend-backend frágil (base URL no resiliente y errores HTTP poco normalizados).
- CORS demasiado restrictivo para peticiones `POST` con JSON.
- Estaciones Bicimad siempre visibles, recargando el mapa.
- Inputs sin sugerencias de origen/destino.
- Tarjeta de estado de ruta con feedback poco claro en errores y estados intermedios.

## Decisiones de corrección
1. **Contratos estables + errores tipados**
   - `POST /api/routes` mantiene contrato del slice, pero ahora normaliza errores con `detail.code` + `detail.message`.
   - Se mapean casos de negocio: origen/destino no encontrado, ruta no encontrada, grafo calentando, modo no disponible.
2. **CORS de desarrollo local explícito**
   - Permitidos `http://localhost:5173` y `http://127.0.0.1:5173`.
   - Métodos `GET`, `POST`, `OPTIONS`.
3. **Sugerencias vía backend (no desde React a Nominatim)**
   - Nuevo endpoint: `GET /api/geocoding/suggest?q=...`.
   - Normalización de payload para UI (`label`, `value`, `lat`, `lon`).
4. **UX de mapa más limpia**
   - Toggle en panel lateral: **“Mostrar estaciones Bicimad”**.
   - Capa Bicimad oculta por defecto.
5. **Modo honesto de producto**
   - Solo modo `Rápida` (API `fastest`) ejecuta cálculo real.
   - Modos futuros siguen bloqueados con mensaje claro.

## Nuevo flujo frontend-backend
1. Usuario escribe origen/destino.
2. Frontend consulta sugerencias con debounce a `/api/geocoding/suggest`.
3. Usuario envía formulario en modo rápida.
4. Frontend llama `POST /api/routes`.
5. Backend:
   - geocodifica origen/destino,
   - carga grafo OSMnx desde caché o descarga,
   - calcula shortest path por `length`,
   - devuelve GeoJSON y resumen.
6. Frontend dibuja ruta, hace fit bounds y actualiza tarjeta de estado.

## Endpoints del slice
- `POST /api/routes`
- `GET /api/geocoding/suggest`

## Criterios de aceptación del fix
- `GET /health` operativo.
- `POST /api/routes` operativo con `mode=fastest`.
- `GET /api/geocoding/suggest` operativo.
- Error opaco “Failed to fetch” reemplazado por mensajes útiles en español.
- Toggle de Bicimad funcional (mostrar/ocultar capa).
- Inputs con sugerencias y selección usable.
- Ruta dibujada y resumen visible cuando hay resultado.

## Verificación manual
1. Arrancar backend y frontend.
2. Comprobar `GET /health`.
3. Probar sugerencias: escribir “Ato” y “Mat” en inputs.
4. Seleccionar sugerencias y lanzar ruta en modo rápida.
5. Verificar:
   - aparece línea en mapa,
   - se ajusta el mapa a la ruta,
   - tarjeta muestra distancia y estado.
6. Activar/desactivar “Mostrar estaciones Bicimad” y confirmar render condicional.
7. Probar errores:
   - backend parado => mensaje “No se pudo conectar con el backend de rutas...”,
   - búsqueda inválida => mensaje de origen/destino no localizado.

## Limitaciones actuales
- Primera carga del grafo puede tardar por descarga inicial (comportamiento esperado).
- Dependencia externa de Nominatim para geocodificación y sugerencias.
- Modos segura/equilibrada/nocturna pendientes de slices posteriores.
