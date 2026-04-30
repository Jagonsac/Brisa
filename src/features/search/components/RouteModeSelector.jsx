import { routeModeByApiMode } from '../../../shared/constants/routeModes';
import styles from './RouteModeSelector.module.css';

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

export function RouteModeSelector({ routesByMode, selectedMode, onSelectMode, loading, compact = false }) {
  const routeModes = Object.keys(routesByMode);

  return (
    <div className={`${styles.container} ${compact ? styles.compact : ""}`}>
      <p className={styles.title}>Elige tu ruta preferida</p>
      <div className={styles.buttonGroup} role="tablist" aria-label="Rutas disponibles en el mapa">
        {routeModes.length === 0 && (
          <p className={styles.emptyState}>{loading ? 'Calculando alternativas...' : 'Aún no hay rutas para comparar.'}</p>
        )}

        {routeModes.map((modeKey) => {
          const route = routesByMode[modeKey];
          const modeMeta = routeModeByApiMode[modeKey];
          const isActive = selectedMode === modeKey;

          return (
            <button
              key={modeKey}
              className={`${styles.modeButton} ${isActive ? styles.modeButtonActive : ''}`}
              type="button"
              onClick={() => onSelectMode(modeKey)}
            >
              <div className={styles.modeHeader}>
                <span className={styles.colorDot} style={{ backgroundColor: modeMeta?.color }} aria-hidden="true" />
                <strong>{modeMeta?.label || modeKey}</strong>
              </div>
              <span>{route?.summary?.distanceKm} km</span>
              <span>{formatDuration(route?.summary?.estimatedDurationMinutes)}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
