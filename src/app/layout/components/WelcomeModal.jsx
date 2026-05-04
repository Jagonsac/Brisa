import { useEffect } from 'react';

import { ROUTE_MODES } from '../../../shared/constants/routeModes';
import styles from './WelcomeModal.module.css';

const KEY_METRICS = [
  'histórico de accidentes ciclistas',
  'intensidad y tipo de tráfico',
  'complejidad de cruces e intersecciones',
  'ancho y tipología de la vía',
  'continuidad y calidad de infraestructura ciclista',
];

export function WelcomeModal({ open, onClose }) {
  useEffect(() => {
    if (!open) return;

    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className={styles.overlay} role="presentation" onClick={onClose}>
      <section
        className={styles.modal}
        role="dialog"
        aria-modal="true"
        aria-labelledby="welcome-modal-title"
        onClick={(event) => event.stopPropagation()}
      >
        <button type="button" className={styles.closeButton} onClick={onClose} aria-label="Cerrar introducción">
          ×
        </button>

        <p className={styles.eyebrow}>👋 Bienvenida/o a Brisa</p>
        <h2 id="welcome-modal-title">Tu copiloto ciclista para moverte más segura/o por Madrid, potenciado por la <span className={styles.iaGradient}>IA</span></h2>

        <p>
          <strong>Brisa</strong> es un proyecto gratuito que te ayuda a elegir rutas en bici de forma fácil, visual y
          con criterio de seguridad real y análisis inteligente de riesgos. Solo tienes que indicar origen y destino y comparar alternativas en segundos.
        </p>

        <p>
          Calculamos cada ruta con datos abiertos del Ayuntamiento de Madrid y capas urbanas combinadas para estimar el{' '}
          <span className={styles.securityTag}>índice de seguridad</span> y el <span className={styles.cyclabilityTag}>índice de ciclabilidad</span>.
        </p>

        <ul className={styles.metricList}>
          {KEY_METRICS.map((metric) => (
            <li key={metric}>{metric}</li>
          ))}
        </ul>

        <p className={styles.modesText}>
          Puedes comparar los modos <span style={{ '--mode-color': ROUTE_MODES.FASTEST.color }} className={styles.modePill}>Rápida</span>,{' '}
          <span style={{ '--mode-color': ROUTE_MODES.SAFE.color }} className={styles.modePill}>Segura</span> y{' '}
          <span style={{ '--mode-color': ROUTE_MODES.BALANCED.color }} className={styles.modePill}>Equilibrada</span>.
          Además, el <span style={{ '--mode-color': ROUTE_MODES.NIGHT.color }} className={styles.modePill}>Modo nocturno</span> tiene en cuenta
          tráfico nocturno, accidentalidad nocturna y luminosidad de las calles para proponer la opción más segura al anochecer.
        </p>

        <p>
          La IA también compara alternativas, detecta puntos de peligro en el trazado y te explica con lenguaje claro por qué una ruta puede ser más segura que otra.
        </p>

        <p>
          También tienes integración con <strong>Bicimad</strong>: Brisa te indica la estación más cercana a tu origen donde
          coger bici y la mejor estación cercana al destino para cerrar el trayecto.
        </p>

        <p>
          Y no te pierdas las dos visualizaciones del mapa (activables/desactivables): capa de{' '}
          <span className={styles.securityTag}>seguridad ciclista</span> y capa de{' '}
          <span className={styles.cyclabilityTag}>ciclabilidad por barrios</span>.
          La primera prioriza riesgo (accidentes, cruces y tráfico), y la segunda combina seguridad + comodidad de infraestructura.
        </p>

        <button type="button" className={styles.ctaButton} onClick={onClose}>
          ¡Vamos allá!
        </button>
      </section>
    </div>
  );
}
