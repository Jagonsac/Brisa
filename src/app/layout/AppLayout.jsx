import { useMemo, useState } from 'react';

import { BicimadStatusCard } from '../../features/bicimad/components/BicimadStatusCard';
import { useBicimadStations } from '../../features/bicimad/hooks/useBicimadStations';
import { MapView } from '../../features/map/components/MapView';
import { ProjectExplainer } from '../../features/projectStatus/components/ProjectExplainer';
import { ProjectStatusPanel } from '../../features/projectStatus/components/ProjectStatusPanel';
import { RouteModeSelector } from '../../features/search/components/RouteModeSelector';
import { RouteSearchForm } from '../../features/search/components/RouteSearchForm';
import { RouteSummaryCard } from '../../features/routing/components/RouteSummaryCard';
import { createRoute } from '../../features/routing/services/routesService';
import { featureFlags } from '../../shared/config/featureFlags';
import { ROUTE_MODES } from '../../shared/constants/routeModes';
import styles from './AppLayout.module.css';

const INITIAL_FORM = {
  origin: '',
  destination: '',
};

export function AppLayout() {
  const [formValues, setFormValues] = useState(INITIAL_FORM);
  const [selectedMode, setSelectedMode] = useState(ROUTE_MODES.FAST);
  const [infoMessage, setInfoMessage] = useState('Selecciona origen y destino para calcular la ruta más corta.');
  const [routeData, setRouteData] = useState(null);
  const [routeError, setRouteError] = useState('');
  const [routeLoading, setRouteLoading] = useState(false);

  const bicimadLayerEnabled = featureFlags.enableBicimad && featureFlags.enableBicimadStationsLayer;
  const bicimadState = useBicimadStations({ enabled: bicimadLayerEnabled });

  const canSubmit = useMemo(
    () => formValues.origin.trim().length > 0 && formValues.destination.trim().length > 0,
    [formValues.destination, formValues.origin],
  );

  const handleChange = (field, value) => {
    setFormValues((previous) => ({ ...previous, [field]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setRouteError('');

    if (!canSubmit) {
      setInfoMessage('Completa origen y destino para preparar la ruta.');
      return;
    }

    if (!selectedMode.available) {
      setRouteData(null);
      setInfoMessage(`El modo ${selectedMode.label.toLowerCase()} llegará en slices posteriores.`);
      return;
    }

    if (!featureFlags.enableRealRouting) {
      setInfoMessage('El cálculo real de rutas está desactivado por feature flag.');
      return;
    }

    setRouteLoading(true);
    setInfoMessage('Calculando ruta real sobre red ciclista de Madrid...');

    try {
      const response = await createRoute({
        originQuery: formValues.origin.trim(),
        destinationQuery: formValues.destination.trim(),
        mode: selectedMode.apiMode,
      });
      setRouteData(response.data);
      setInfoMessage(`Ruta ${selectedMode.label.toLowerCase()} calculada correctamente.`);
    } catch (error) {
      setRouteData(null);
      setRouteError(error instanceof Error ? error.message : 'No fue posible calcular la ruta.');
      setInfoMessage('Revisa los datos e inténtalo de nuevo.');
    } finally {
      setRouteLoading(false);
    }
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
              <RouteSearchForm formValues={formValues} onFieldChange={handleChange} onSubmit={handleSubmit} loading={routeLoading} />
              <RouteModeSelector selectedMode={selectedMode} onSelectMode={setSelectedMode} />
              <p className={styles.infoText}>{infoMessage}</p>
              <RouteSummaryCard
                routeData={routeData}
                loading={routeLoading}
                error={routeError}
                statusMessage={routeData ? 'Ruta calculada y dibujada en el mapa.' : 'Sin ruta calculada todavía.'}
              />
            </section>
          )}

          <BicimadStatusCard
            enabled={bicimadLayerEnabled}
            loading={bicimadState.loading}
            error={bicimadState.error}
            source={bicimadState.source}
            usedFallback={bicimadState.usedFallback}
            stationsCount={bicimadState.stations.length}
          />

          {featureFlags.enableProjectStatusPanel && <ProjectStatusPanel />}
        </aside>

        <section className={styles.mapContainer}>
          {featureFlags.enableMap ? (
            <MapView
              selectedMode={selectedMode}
              bicimadStations={bicimadState.stations}
              showBicimadLayer={bicimadLayerEnabled}
              routeData={routeData}
            />
          ) : (
            <p>Mapa desactivado por feature flag.</p>
          )}
        </section>
      </main>
    </div>
  );
}
