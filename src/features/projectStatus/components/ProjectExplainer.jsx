import styles from './ProjectExplainer.module.css';

export function ProjectExplainer() {
  return (
    <section className={styles.card}>
      <h2>¿Qué es Brisa?</h2>
      <p>
        Brisa es una app para ayudar a moverse por Madrid en bicicleta priorizando seguridad, claridad y decisión informada.
      </p>
      <p>
        Este Slice 1 establece la base técnica: interfaz funcional, mapa interactivo, estructura modular y contratos para crecer sin caos.
      </p>
    </section>
  );
}
