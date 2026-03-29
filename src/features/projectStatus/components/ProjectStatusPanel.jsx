import { projectStatusData } from '../../../mocks/projectStatusData';
import styles from './ProjectStatusPanel.module.css';

export function ProjectStatusPanel() {
  return (
    <section className={styles.panel}>
      <h2>Estado del proyecto</h2>
      <ul>
        {projectStatusData.map((item) => (
          <li key={item.id}>
            <span className={`${styles.badge} ${item.done ? styles.done : styles.pending}`}>
              {item.done ? 'Listo' : 'Pendiente'}
            </span>
            <span>{item.label}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
