import { routeModeOptions } from '../../../shared/constants/routeModes';
import styles from './RouteModeSelector.module.css';

export function RouteModeSelector({ selectedMode, onSelectMode }) {
  return (
    <div className={styles.container}>
      <p className={styles.title}>Modo de ruta</p>
      <div className={styles.buttonGroup} role="tablist" aria-label="Modos de ruta disponibles">
        {routeModeOptions.map((mode) => {
          const isActive = selectedMode.key === mode.key;
          return (
            <button
              key={mode.key}
              className={`${styles.modeButton} ${isActive ? styles.modeButtonActive : ''}`}
              type="button"
              onClick={() => onSelectMode(mode)}
            >
              {mode.label}
              {!mode.available && <span className={styles.comingSoon}>Próximamente</span>}
            </button>
          );
        })}
      </div>
    </div>
  );
}
