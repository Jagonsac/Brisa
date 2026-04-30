# Contributing to Brisa

¡Gracias por tu interés en contribuir a Brisa!

## Flujo recomendado

1. Abre un issue para discutir el cambio (bug, mejora o feature).
2. Crea una rama desde `main`.
3. Implementa cambios pequeños y enfocados.
4. Ejecuta checks locales:
   - Frontend: `npm run lint && npm run build`
   - Backend: `cd backend && pytest`
5. Actualiza documentación/contratos si cambia comportamiento público.
6. Abre Pull Request con contexto claro y pasos de validación.

## Estándares

- Mantén frontend y backend desacoplados por contratos.
- No mover lógica GIS/scoring al frontend.
- Prioriza legibilidad y modularidad.
- Evita mezclar cambios no relacionados en un mismo PR.

## Cambios de API

Si modificas request/response:
- Actualiza `docs/contracts`.
- Refleja cambios en `README.md`/`backend/README.md` si aplica.

## Reporte de bugs

Incluye:
- comportamiento esperado vs actual
- pasos de reproducción
- entorno (SO, navegador, versión Python/Node)
- logs o capturas relevantes

