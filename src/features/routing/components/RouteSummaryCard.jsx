import styles from './RouteSummaryCard.module.css';

export function RouteSummaryCard({ routeData, loading, error, statusMessage }) {
  const distanceKm = routeData?.summary?.distanceKm;

  return (
    <section className={styles.card}>
      <h3>Ruta actual</h3>
      <p className={styles.status}>{statusMessage}</p>
      {loading && <p className={styles.loading}>Calculando ruta sobre red ciclista de Madrid...</p>}
      {error && <p className={styles.error}>{error}</p>}
      {routeData && !loading && !error && (
        <dl className={styles.summaryList}>
          <div>
            <dt>Distancia</dt>
            <dd>{distanceKm} km</dd>
          </div>
          <div>
            <dt>Modo</dt>
            <dd>{routeData.routeGeoJson.properties.mode}</dd>
          </div>
          <div>
            <dt>Perfil</dt>
            <dd>{routeData.routeGeoJson.properties.profile}</dd>
          </div>
        </dl>
      )}
    </section>
  );
}
