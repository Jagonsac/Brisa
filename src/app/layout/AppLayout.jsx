import { useMemo, useState } from 'react';

import { MapView } from '../../features/map/components/MapView';
import { ProjectExplainer } from '../../features/projectStatus/components/ProjectExplainer';
import { ProjectStatusPanel } from '../../features/projectStatus/components/ProjectStatusPanel';
import { RouteModeSelector } from '../../features/search/components/RouteModeSelector';
import { RouteSearchForm } from '../../features/search/components/RouteSearchForm';
import { featureFlags } from '../../shared/config/featureFlags';
import { ROUTE_MODES } from '../../shared/constants/routeModes';
import styles from './AppLayout.module.css';

const INITIAL_FORM = {
  origin: '',
  destination: '',
};

export function AppLayout() {
  const [formValues, setFormValues] = useState(INITIAL_FORM);
  const [selectedMode, setSelectedMode] = useState(ROUTE_MODES.BALANCED);
  const [infoMessage, setInfoMessage] = useState('El motor de rutas reales llegará en próximos slices.');

  const canSubmit = useMemo(
    () => formValues.origin.trim().length > 0 && formValues.destination.trim().length > 0,
    [formValues.destination, formValues.origin],
  );

  const handleChange = (field, value) => {
    setFormValues((previous) => ({ ...previous, [field]: value }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!canSubmit) {
      setInfoMessage('Completa origen y destino para preparar la ruta.');
      return;
    }

    setInfoMessage(
      `Ruta ${selectedMode.label.toLowerCase()} preparada a nivel de interfaz. El cálculo real se activa en el Slice 4.`,
    );
  };

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1>Brisa</h1>
        <p>Plataforma para planificar rutas ciclistas más seguras por Madrid.</p>
      </header>

      <main className={styles.mainLayout}>
        <aside className={styles.sidebar}>
          <ProjectExplainer />

          {featureFlags.enableSearchUi && (
            <section className={styles.panelCard}>
              <h2>Preparación de ruta</h2>
              <RouteSearchForm formValues={formValues} onFieldChange={handleChange} onSubmit={handleSubmit} />
              <RouteModeSelector selectedMode={selectedMode} onSelectMode={setSelectedMode} />
              <p className={styles.infoText}>{infoMessage}</p>
            </section>
          )}

          {featureFlags.enableProjectStatusPanel && <ProjectStatusPanel />}
        </aside>

        <section className={styles.mapContainer}>
          {featureFlags.enableMap ? <MapView selectedMode={selectedMode} /> : <p>Mapa desactivado por feature flag.</p>}
        </section>
      </main>
    </div>
  );
}
