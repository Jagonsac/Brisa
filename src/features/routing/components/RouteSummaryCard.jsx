import { featureFlags } from '../../../shared/config/featureFlags';
import { routeModeByApiMode } from '../../../shared/constants/routeModes';
import styles from './RouteSummaryCard.module.css';

function formatDuration(minutes) {
  if (!Number.isFinite(minutes)) {
    return '--';
  }

  const roundedMinutes = Math.max(1, Math.round(minutes));
  if (roundedMinutes < 60) {
    return `${roundedMinutes} min`;
  }

  const hours = Math.floor(roundedMinutes / 60);
  const remainingMinutes = roundedMinutes % 60;

  if (remainingMinutes === 0) {
    return `${hours} h`;
  }

  return `${hours} h ${remainingMinutes} min`;
}

export function RouteSummaryCard({ selectedRoute, routesByMode, selectedMode, loading, error, statusMessage }) {
  const summary = selectedRoute?.summary;
  const modeMeta = routeModeByApiMode[selectedMode];
  const explanations = featureFlags.enableRouteExplanations ? selectedRoute?.explanations || [] : [];

  let toneClass = styles.info;
  if (loading) toneClass = styles.loading;
  if (error) toneClass = styles.warning;
  if (selectedRoute && !error && !loading) toneClass = styles.success;

  return (
    <section className={styles.card}>
      <h3>Comparativa de rutas</h3>
      <p className={`${styles.status} ${toneClass}`}>{loading ? 'Calculando rutas rápida, segura y equilibrada...' : error || statusMessage}</p>

      {Object.keys(routesByMode).length > 0 && (
        <div className={styles.pills}>
          {Object.keys(routesByMode).map((modeKey) => {
            const currentModeMeta = routeModeByApiMode[modeKey];
            const isSelected = selectedMode === modeKey;

            return (
              <span
                className={`${styles.pill} ${isSelected ? styles.pillActive : ''}`}
                key={modeKey}
                style={{ '--pill-color': currentModeMeta?.color || '#6b7fa4' }}
              >
                {currentModeMeta?.label || modeKey}
              </span>
            );
          })}
        </div>
      )}

      {selectedRoute && !loading && !error && (
        <>
          <dl className={styles.summaryList}>
            <div>
              <dt>Ruta activa</dt>
              <dd style={{ color: modeMeta?.color }}>{modeMeta?.label || selectedMode}</dd>
            </div>
            <div>
              <dt>Distancia</dt>
              <dd>{summary?.distanceKm} km</dd>
            </div>
            <div>
              <dt>Tiempo</dt>
              <dd>{formatDuration(summary?.estimatedDurationMinutes)}</dd>
            </div>
            <div>
              <dt>Seguridad</dt>
              <dd>{summary?.relativeSafety || '-'}</dd>
            </div>
            <div>
              <dt>Iluminación</dt>
              <dd>{summary?.lightingQuality || '-'}</dd>
            </div>
            <div>
              <dt>Riesgo nocturno</dt>
              <dd>{summary?.nightRisk || '-'}</dd>
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
