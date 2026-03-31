# Slice 4 — Routing real corregido y pulido (FastAPI + OSMnx)

## Problemas detectados
- Bug de selección en sugerencias por cierre prematuro en blur/click.
- Inputs mezclaban texto visible y lugar seleccionado, provocando estados ambiguos.
- Cálculo de ruta sensible a queries ambiguas cuando no se consolidaba selección.
- Marcadores demo permanentes ensuciaban el mapa.
- El mapa no mostraba origen/destino hasta después del cálculo.

## Decisiones de corrección
1. **Estado separado por campo (input vs place seleccionado)**
   - Frontend mantiene para `origin` y `destination`:
     - valor visible del input,
     - entidad seleccionada (`label`, `value`, `lat`, `lon`),
     - estado de dropdown abierto/cerrado.
   - Si el usuario edita manualmente tras seleccionar, se invalida el place seleccionado.
2. **Selección robusta de sugerencias sin blur prematuro**
   - La selección usa `onMouseDown` en cada opción para consolidar antes del `blur`.
   - Al seleccionar:
     - se actualiza input,
     - se guarda place seleccionado,
     - se cierra el dropdown,
     - se evita re-fetch inmediato con flag de actualización programática.
3. **Contrato de rutas más robusto**
   - `POST /api/routes` recibe `origin` y `destination` como objetos con `query` + `lat/lon` opcionales.
   - Backend prioriza coordenadas si existen; si no, hace fallback a geocoding por `query`.
4. **UX de mapa limpia y profesional**
   - Se eliminan pins demo por defecto.
   - Pins de origen/destino se dibujan al seleccionar sugerencias, incluso sin ruta calculada.
   - La ruta (si existe) convive con pins y ajuste de bounds.
5. **Bicimad se mantiene opcional**
   - Toggle de Bicimad no se altera y sigue oculto por defecto.

## Flujo frontend-backend actualizado
1. Usuario escribe en origen/destino.
2. Frontend consulta sugerencias con debounce a `GET /api/geocoding/suggest`.
3. Usuario selecciona una sugerencia (consolidación estable por `onMouseDown`).
4. Frontend guarda place seleccionado y muestra pin inmediato en mapa.
5. Al enviar formulario:
   - si hay selección: se envían `lat/lon` + `query`,
   - si no hay selección: se envía solo `query` y backend geocodifica.
6. Backend resuelve puntos, hace snap a la red bike y calcula shortest-path por `length`.

## Endpoints del slice
- `POST /api/routes`
- `GET /api/geocoding/suggest`

## Criterios de aceptación del fix
- Sugerencias seleccionables sin perder click por blur.
- Input actualizado tras seleccionar y dropdown cerrado.
- Sin re-fetch inmediato al consolidar selección.
- Pins de origen/destino visibles antes de calcular ruta.
- Sin marcadores demo por defecto.
- `POST /api/routes` prioriza coordenadas seleccionadas.
- Mensajes de error en español orientados a acción.
- Toggle Bicimad funcional.

## Verificación manual
1. Arrancar backend y frontend.
2. En origen escribir `Plaza de Castilla` y seleccionar una sugerencia.
3. Verificar que:
   - el input queda rellenado,
   - dropdown se cierra,
   - aparece pin de origen.
4. En destino escribir `Matadero Madrid`, seleccionar sugerencia y verificar pin de destino.
5. Pulsar **Calcular ruta** en modo rápida y comprobar:
   - ruta visible,
   - pins siguen visibles,
   - tarjeta muestra distancia.
6. Editar manualmente origen/destino tras seleccionar:
   - se invalida selección,
   - desaparece el pin correspondiente,
   - vuelven sugerencias al enfocar/escribir.
7. Activar/desactivar toggle Bicimad y verificar capa condicional.

## Limitaciones actuales
- Primera carga del grafo puede tardar por descarga inicial.
- Dependencia externa de Nominatim para sugerencias/geocoding.
- Modos segura/equilibrada/nocturna pendientes de slices posteriores.

## Ajustes de contrato y coordenadas (hardening)
- `POST /api/routes` ahora acepta dos formatos de entrada:
  - **Recomendado**: `origin/destination` con `query` y `lat/lon` opcionales.
  - **Legado**: `originQuery/destinationQuery` para mantener compatibilidad.
- El router transforma ambos formatos a una estructura interna única antes del cálculo.
- Política de errores afinada:
  - `400` para datos de negocio incompletos (por ejemplo, faltan origen/destino/modo).
  - `404` cuando origen o destino no se puede localizar o no existe ruta válida.
  - `400` para payload inconsistente o datos insuficientes (por ejemplo, `lat` sin `lon`).
- Sugerencias conservan direcciones específicas con número:
  - `displayText` prioriza `road + house_number` cuando Nominatim lo devuelve.
  - Se mantiene `label` completo para contexto y `value` como alias retrocompatible.
- Orden de coordenadas verificado de extremo a extremo:
  - Selección/markers en Leaflet: `[lat, lon]`.
  - Snap en OSMnx `nearest_nodes`: `X=lon`, `Y=lat`.
  - GeoJSON `LineString`: `[lon, lat]`.

## Hardening adicional del request de rutas (fix 422 definitivo)
- El router ya **no valida el body con un schema rígido en la firma**.
- `POST /api/routes` recibe `payload: dict` y ejecuta `parse_route_payload(payload)` en backend para normalizar.
- Formatos soportados: 
  - A: `origin/destination` con `query` + `lat/lon` opcionales.
  - B: `originQuery/destinationQuery`.
  - C: `origin/destination` con solo `query`.
- `lat/lon` aceptan `number` o `string` convertible.
- Validación de negocio devuelve `400` con mensaje útil cuando faltan datos; evita `422` en payloads razonables.
- El parseo interno genera una estructura única estable para el servicio de rutas.
