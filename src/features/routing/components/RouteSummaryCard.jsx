import { featureFlags } from '../../../shared/config/featureFlags';
import styles from './RouteSummaryCard.module.css';

const modeLabels = {
  fastest: 'Rápida',
  safe: 'Segura',
  balanced: 'Equilibrada',
  night: 'Nocturna',
};

export function RouteSummaryCard({ routeData, loading, error, statusMessage }) {
  const summary = routeData?.summary;
  const mode = summary?.mode || routeData?.routeGeoJson?.properties?.mode;
  const explanations = featureFlags.enableRouteExplanations ? routeData?.explanations || [] : [];

  let toneClass = styles.info;
  if (loading) toneClass = styles.loading;
  if (error) toneClass = styles.warning;
  if (routeData && !error && !loading) toneClass = styles.success;

  return (
    <section className={styles.card}>
      <h3>Ruta actual</h3>
      <p className={`${styles.status} ${toneClass}`}>{loading ? 'Calculando ruta...' : error || statusMessage}</p>

      {routeData && !loading && !error && (
        <>
          <dl className={styles.summaryList}>
            <div>
              <dt>Distancia</dt>
              <dd>{summary?.distanceKm} km</dd>
            </div>
            <div>
              <dt>Modo</dt>
              <dd>{modeLabels[mode] || mode}</dd>
            </div>
            <div>
              <dt>Seguridad</dt>
              <dd>{summary?.relativeSafety || '-'}</dd>
            </div>
            <div>
              <dt>Iluminación</dt>
              <dd>{summary?.lightingQuality || '-'}</dd>
            </div>
          </dl>

          {explanations.length > 0 && (
            <ul className={styles.explanations}>
              {explanations.map((message, index) => (
                <li key={`${message}-${index}`}>{message}</li>
              ))}
            </ul>
          )}
        </>
      )}
    </section>
  );
}
