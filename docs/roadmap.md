# Evolución del producto y roadmap

## Estado actual

Brisa ha completado nueve fases internas de desarrollo y cuenta con una base funcional integral para planificación ciclista en Madrid.

## Capacidades entregadas (resumen unificado)

1. **Experiencia base de mapa y UX de búsqueda.**
2. **Integración de estaciones Bicimad usando snapshot local estable.**
3. **Backend API estable para health, estaciones y rutas.**
4. **Routing shortest-path real sobre OSMnx.**
5. **Capa de seguridad (grid + resumen) y visualización en frontend.**
6. **Routing multicriterio seguro/nocturno con explicaciones deterministas.**
7. **Índice de ciclabilidad por barrio (ranking, detalle y comparación).**
8. **Routing multimodal con Bicimad (segmentación por modo).**
9. **Consolidación funcional y preparación para operación continua.**

## Próxima etapa (open source y madurez)

### Prioridad alta
- Estabilizar documentación pública y guías de contribución.
- Ampliar cobertura de tests de integración E2E frontend-backend.
- Versionado semántico y política de releases.

### Prioridad media
- CI/CD pública (lint + build + tests backend) con checks obligatorios.
- Observabilidad básica (latencias, errores por endpoint, salud de proveedores).
- Optimización incremental de precálculos/caches GIS.
- Reintroducir `station_status` en multimodal Bicimad como optimización no bloqueante (ranking por disponibilidad y replanificación), manteniendo fallback determinista por cercanía cuando falle el dato en vivo.
- Diseñar e integrar un dataset de estaciones Bicimad en vivo con `bicis_disponibles` y `anclajes_disponibles`, con caché y degradación controlada a snapshot.

### Prioridad baja
- Internacionalización (ES/EN) de interfaz y documentación.
- Mejoras de accesibilidad AA en paneles y controles del mapa.
- Dataset complementario para enriquecer criterios de seguridad.

## Historial detallado

El detalle histórico por fase se conserva en `docs/slices/` como archivo de decisiones y contexto de implementación.
