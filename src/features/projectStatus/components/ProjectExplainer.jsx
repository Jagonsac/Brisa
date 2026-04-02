import styles from './ProjectExplainer.module.css';

export function ProjectExplainer() {
  return (
    <section className={styles.card}>
      <h2>¿Qué es Brisa?</h2>
      <p>
        Brisa es una app para ayudar a moverse por Madrid en bicicleta priorizando seguridad, claridad y decisión informada.
      </p>
      <p>
        Combina rutas más rápidas con una capa de seguridad por barrios, estado de estaciones BiciMAD y resúmenes claros para elegir
        mejor cada trayecto.
      </p>
    </section>
  );
}
