import styles from './SafetyLegend.module.css';

export function SafetyLegend({ visible, summary }) {
  if (!visible) return null;

  return (
    <div className={styles.legend}>
      <h4>Seguridad Ciclista</h4>
      <div className={styles.scale}>
        <span className={styles.low}>Menos segura</span>
        <span className={styles.mid}>Intermedia</span>
        <span className={styles.high}>Más segura</span>
      </div>
      <p>
        Score {summary?.scoreMin ?? 0}–{summary?.scoreMax ?? 100} · {summary?.cellCount ?? 0} celdas
      </p>
    </div>
  );
}
