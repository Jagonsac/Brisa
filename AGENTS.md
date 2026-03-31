# AGENTS.md — Guía operativa para agentes en Brisa

## Visión general
Brisa es una app web para movilidad ciclista segura en Madrid. El proyecto evoluciona por slices funcionales pequeños, visibles y documentados.

## Objetivo actual
Slice 3: backend mínimo FastAPI integrado con frontend, contratos y fallback documentados.

## Reglas del repositorio
1. Un slice = una vertical pequeña y funcional.
2. No avanzar un slice sin demo visible.
3. No mezclar cambios de múltiples slices en un único PR.
4. Mantener frontend y backend desacoplados mediante contratos.
5. Documentar contratos antes de implementar integraciones.

## Principios de arquitectura
- Separación en capas: `app`, `features`, `shared`, `mocks`, `docs`, `backend`.
- Lógica de negocio fuera de componentes visuales.
- Endpoints con routers finos + servicios dedicados.
- Feature flags para activar valor incremental sin romper demos.
- Evitar archivos grandes y responsabilidades difusas.

## Cómo trabajar por slices
1. Leer `docs/roadmap.md` y el documento del slice activo.
2. Definir alcance mínimo demoable.
3. Implementar en la feature/capa correspondiente.
4. Actualizar contratos/documentación si cambia la interfaz de datos.
5. Ejecutar checks (`lint`, `build` y validación backend cuando aplique).

## Backend (Slice 3 en adelante)
- El backend vive en `backend/app`.
- Añadir endpoints nuevos en `backend/app/routers` y delegar lógica a `backend/app/services`.
- El consumo de proveedores externos debe ir en `backend/app/clients`.
- La normalización de payloads externos debe ir en `backend/app/utils`.
- Mantener estables los contratos JSON documentados en `docs/contracts`.

## Contratos
- Los contratos viven en `docs/contracts`.
- Cualquier cambio de campos JSON debe reflejarse en contratos y docs del slice.
- El frontend debe consumir contratos internos estables, no payloads crudos de proveedor.

## Convenciones de nombres
- Componentes frontend: `PascalCase.jsx`
- Estilos por componente: `Nombre.module.css`
- Constantes/config frontend: `camelCase.js` con exports explícitos
- Features frontend: carpeta en `camelCase` semántico
- Módulos backend Python: `snake_case.py`

## Cómo documentar cambios
- Actualizar `docs/slices/slice-X.md` con decisiones y criterios.
- Si cambia arquitectura, tocar `docs/architecture.md`.
- Si cambia prioridad de producto, tocar `docs/roadmap.md`.
- Si cambia interfaz HTTP, actualizar `docs/contracts`.

## Regla de modularidad
- Cada feature/servicio debe poder evolucionar con mínimo impacto en otros.
- Reutilización transversal frontend vía `shared`.
- Reutilización backend vía `services` y `utils`, no en routers.

## Checklist antes de cerrar un slice
- [ ] Demo visible y estable.
- [ ] Feature flags revisadas.
- [ ] Contratos alineados con UI/API esperada.
- [ ] Documentación del slice actualizada.
- [ ] README actualizado si cambia experiencia de uso.
- [ ] Lint/build ejecutados (o limitación documentada).
