import styles from './RouteSummaryCard.module.css';

export function RouteSummaryCard({ routeData, loading, error, statusMessage }) {
  const distanceKm = routeData?.summary?.distanceKm;

  let toneClass = styles.info;
  if (loading) toneClass = styles.loading;
  if (error) toneClass = styles.warning;
  if (routeData && !error && !loading) toneClass = styles.success;

  return (
    <section className={styles.card}>
      <h3>Ruta actual</h3>
      <p className={`${styles.status} ${toneClass}`}>{loading ? 'Calculando ruta...' : error || statusMessage}</p>

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
            <dt>Origen / destino</dt>
            <dd className={styles.compact}>Listos en mapa</dd>
          </div>
        </dl>
      )}
    </section>
  );
}
