import { useState } from 'react';
import styles from './AiRouteInsightsPanel.module.css';

export function AiRouteInsightsPanel({ insights, loading, error, onAnalyze, onClose, open, disabled, isMobile = false }) {
  const [expanded, setExpanded] = useState(false);

  const title = 'ANÁLISIS DE RUTA Y DETECCIÓN DE PUNTOS DE PELIGRO';

  if (!open) {
    return (
      <section className={`${styles.card} ${isMobile ? styles.mobileAnchor : styles.desktopAnchor}`}>
        <button type="button" disabled={disabled || loading} onClick={onAnalyze} className={styles.cta}>
          {loading ? 'ANALIZANDO RUTAS…' : 'ANALIZAR RUTAS CON IA'}
        </button>
      </section>
    );
  }

  return (
    <section className={`${styles.card} ${isMobile ? styles.mobileOpen : styles.desktopOpen} ${expanded ? styles.expanded : ''}`}>
      <div className={styles.headerRow}>
        <h3>{title}</h3>
        <div className={styles.actions}>
          {!isMobile && (
            <button type="button" onClick={() => setExpanded((value) => !value)} className={styles.secondaryButton}>
              {expanded ? 'MINIMIZAR' : 'AMPLIAR'}
            </button>
          )}
          <button type="button" onClick={onClose} className={styles.closeButton}>CERRAR</button>
        </div>
      </div>
      <div className={styles.content}>
        {loading && <p>ANALIZANDO RUTAS…</p>}
        {error && <p className={styles.error}>{error}</p>}
        {insights?.overview && <p className={styles.overview}>{insights.overview}</p>}
        {Array.isArray(insights?.routes) && insights.routes.map((route) => (
          <article key={route.mode} className={styles.routeBlock}>
            <h4>{String(route.mode || '').toUpperCase()}</h4>
            <p><strong>LO MEJOR:</strong> {route.best}</p>
            <p><strong>A VIGILAR:</strong> {route.worst}</p>
            <ul>{(route.tips || []).map((tip, i) => <li key={`${route.mode}-${i}`}>{tip}</li>)}</ul>
          </article>
        ))}
      </div>
    </section>
  );
}
