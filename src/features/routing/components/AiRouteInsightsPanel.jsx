import styles from './AiRouteInsightsPanel.module.css';

export function AiRouteInsightsPanel({ insights, loading, error, onAnalyze, onClose, open, disabled }) {
  return (
    <section className={styles.card}>
      <div className={styles.headerRow}>
        <h3>Copiloto IA</h3>
        {open && <button type="button" onClick={onClose} className={styles.closeButton}>Cerrar</button>}
      </div>
      {!open ? (
        <button type="button" disabled={disabled || loading} onClick={onAnalyze} className={styles.cta}>
          {loading ? 'Analizando rutas…' : 'Comparar rutas y evaluar riesgos con IA'}
        </button>
      ) : (
        <div className={styles.content}>
          {loading && <p>Analizando rutas…</p>}
          {error && <p className={styles.error}>{error}</p>}
          {insights?.overview && <p className={styles.overview}>{insights.overview}</p>}
          {Array.isArray(insights?.routes) && insights.routes.map((route) => (
            <article key={route.mode} className={styles.routeBlock}>
              <h4>{route.mode}</h4>
              <p><strong>Lo mejor:</strong> {route.best}</p>
              <p><strong>A vigilar:</strong> {route.worst}</p>
              <ul>{(route.tips || []).map((tip, i) => <li key={`${route.mode}-${i}`}>{tip}</li>)}</ul>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
