# AGENTS.md — Guía operativa para agentes en Brisa

## Contexto

Brisa es una plataforma web para planificación ciclista segura en Madrid. El repositorio está preparado para colaboración abierta y evolución incremental por capacidades de producto.

## Objetivo de trabajo

Mantener una base de código estable, modular y documentada, preservando contratos entre frontend y backend y evitando regresiones funcionales.

## Reglas del repositorio

1. Mantener cambios acotados, trazables y con demo/verificación clara.
2. No mezclar refactors amplios con cambios funcionales no relacionados.
3. Mantener frontend y backend desacoplados mediante contratos documentados.
4. Actualizar documentación en el mismo cambio cuando se altere comportamiento público.
5. Ejecutar checks de calidad (`lint`, `build`, `pytest`) cuando aplique.

## Principios de arquitectura

- Separación en capas: `app`, `features`, `shared`, `mocks`, `docs`, `backend`.
- Lógica de negocio fuera de componentes visuales.
- Endpoints con routers finos + servicios dedicados.
- Reutilización backend en `services` y `utils`; no incrustar reglas en routers.
- Evitar archivos grandes y responsabilidades difusas.

## Reglas backend

- Nuevos endpoints en `backend/app/routers`.
- Lógica de dominio en `backend/app/services`.
- Integraciones externas en `backend/app/clients`.
- Normalización de payloads externos en `backend/app/utils`.
- Mantener contratos JSON alineados con `docs/contracts`.

## Reglas de routing/safety

- No mover lógica GIS/scoring al frontend React.
- `POST /api/routes` se mantiene como endpoint principal de routing.
- Pesos/criterios por edge viven en servicios backend dedicados.
- Reutilizar caches en `backend/data/routing` y `backend/data/safety/processed`.
- Explicabilidad de rutas siempre determinista y basada en métricas reales.

## Contratos y documentación

- Cualquier cambio en interfaz HTTP debe actualizar `docs/contracts`.
- Si cambia arquitectura o flujo funcional, actualizar `docs/architecture.md` y/o `docs/roadmap.md`.
- Mantener `README.md` y `backend/README.md` consistentes con el estado real del proyecto.

## Convenciones de nombres

- Componentes frontend: `PascalCase.jsx`
- Estilos por componente: `Nombre.module.css`
- Config/constantes frontend: `camelCase.js`
- Features frontend: carpetas en `camelCase`
- Módulos backend Python: `snake_case.py`

## Checklist antes de cerrar cambios

- [ ] Funcionalidad verificada localmente (o limitación documentada).
- [ ] Contratos alineados con frontend/backend.
- [ ] Documentación actualizada.
- [ ] Lint/build/tests ejecutados según alcance.

