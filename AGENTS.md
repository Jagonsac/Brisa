# AGENTS.md — Guía operativa para agentes en Brisa

## Visión general
Brisa es una app web para movilidad ciclista segura en Madrid. El proyecto evoluciona por slices funcionales pequeños, visibles y documentados.

## Objetivo actual
Slice 1: base técnica sólida, mapa funcional, UI inicial y documentación de arquitectura/contratos.

## Reglas del repositorio
1. Un slice = una vertical pequeña y funcional.
2. No avanzar un slice sin demo visible.
3. No mezclar cambios de múltiples slices en un único PR.
4. Mantener el frontend desacoplado del backend mediante contratos.
5. Documentar contratos antes de implementar integraciones.

## Principios de arquitectura
- Separación en capas: `app`, `features`, `shared`, `mocks`, `docs`.
- Lógica de negocio fuera de componentes visuales.
- Feature flags para activar valor incremental sin romper demos.
- Evitar archivos grandes y responsabilidades difusas.

## Cómo trabajar por slices
1. Leer `docs/roadmap.md` y el documento del slice activo.
2. Definir alcance mínimo demoable.
3. Implementar en la feature correspondiente.
4. Actualizar contratos/documentación si cambia la interfaz de datos.
5. Ejecutar checks (`lint`, `build` cuando aplique).

## Qué no hacer
- No meter todo en `App.jsx`.
- No introducir backend acoplado en frontend.
- No añadir dependencias sin justificar valor.
- No dejar TODOs críticos sin registrar en docs del slice.

## Contratos
- Los contratos viven en `docs/contracts`.
- Cualquier cambio de campos JSON debe reflejarse en contratos y docs del slice.
- Si el backend no está listo, usar `mocks/` alineados con esos contratos.

## Convenciones de nombres
- Componentes: `PascalCase.jsx`
- Estilos por componente: `Nombre.module.css`
- Constantes/config: `camelCase.js` con exports explícitos
- Features: carpeta en `camelCase` semántico

## Cómo documentar cambios
- Actualizar `docs/slices/slice-X.md` con decisiones y criterios.
- Si cambia arquitectura, tocar `docs/architecture.md`.
- Si cambia prioridad de producto, tocar `docs/roadmap.md`.

## Regla de modularidad
- Cada feature debe poder evolucionar con mínimo impacto en otras.
- Reutilización transversal solo vía `shared`.

## Checklist antes de cerrar un slice
- [ ] Demo visible y estable.
- [ ] Feature flags revisadas.
- [ ] Contratos alineados con UI/API esperada.
- [ ] Documentación del slice actualizada.
- [ ] README actualizado si cambia experiencia de uso.
- [ ] Lint/build ejecutados (o limitación documentada).
