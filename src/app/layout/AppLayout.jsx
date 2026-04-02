import { useEffect, useMemo, useRef, useState } from 'react';

import { BicimadStatusCard } from '../../features/bicimad/components/BicimadStatusCard';
import { useBicimadStations } from '../../features/bicimad/hooks/useBicimadStations';
import { MapView } from '../../features/map/components/MapView';
import { ProjectExplainer } from '../../features/projectStatus/components/ProjectExplainer';
import { ProjectStatusPanel } from '../../features/projectStatus/components/ProjectStatusPanel';
import { RouteModeSelector } from '../../features/search/components/RouteModeSelector';
import { RouteSearchForm } from '../../features/search/components/RouteSearchForm';
import { getLocationSuggestions } from '../../features/search/services/geocodingService';
import { RouteSummaryCard } from '../../features/routing/components/RouteSummaryCard';
import { useSafetyLayer } from '../../features/safety/hooks/useSafetyLayer';
import { createRoute, waitForRoutingBackendReady } from '../../features/routing/services/routesService';
import { featureFlags } from '../../shared/config/featureFlags';
import { ROUTE_MODES } from '../../shared/constants/routeModes';
import styles from './AppLayout.module.css';

const INITIAL_INPUT_VALUES = {
  origin: '',
  destination: '',
};

const INITIAL_SUGGESTIONS = {
  origin: [],
  destination: [],
};

const INITIAL_LOADING = {
  origin: false,
  destination: false,
};

const INITIAL_SUGGESTION_OPEN = {
  origin: false,
  destination: false,
};

const INITIAL_SELECTED_PLACES = {
  origin: null,
  destination: null,
};

export function AppLayout() {
  const [appBooting, setAppBooting] = useState(true);
  const [bootProgress, setBootProgress] = useState(8);
  const [bootMessage, setBootMessage] = useState('Inicializando motor de rutas...');
  const [inputValues, setInputValues] = useState(INITIAL_INPUT_VALUES);
  const [selectedPlaces, setSelectedPlaces] = useState(INITIAL_SELECTED_PLACES);
  const [selectedMode, setSelectedMode] = useState(ROUTE_MODES.FAST);
  const [infoMessage, setInfoMessage] = useState('Selecciona origen y destino para calcular una ruta ciclista.');
  const [routeData, setRouteData] = useState(null);
  const [routeError, setRouteError] = useState('');
  const [routeLoading, setRouteLoading] = useState(false);
  const [showBicimadLayer, setShowBicimadLayer] = useState(false);
  const [showSafetyLayer, setShowSafetyLayer] = useState(true);
  const [suggestions, setSuggestions] = useState(INITIAL_SUGGESTIONS);
  const [suggestionLoading, setSuggestionLoading] = useState(INITIAL_LOADING);
  const [suggestionOpen, setSuggestionOpen] = useState(INITIAL_SUGGESTION_OPEN);
  const isProgrammaticSelectionRef = useRef({ origin: false, destination: false });

  const bicimadLayerEnabled = featureFlags.enableBicimad && featureFlags.enableBicimadStationsLayer;
  const safetyLayerEnabled = featureFlags.enableSafetyLayer;
  const safetySummaryEnabled = featureFlags.enableSafetySummary;
  const bicimadState = useBicimadStations({ enabled: bicimadLayerEnabled });
  const safetyState = useSafetyLayer({ enabled: safetyLayerEnabled || safetySummaryEnabled });

  const canSubmit = useMemo(
    () => inputValues.origin.trim().length > 0 && inputValues.destination.trim().length > 0,
    [inputValues.destination, inputValues.origin],
  );

  useEffect(() => {
    let isMounted = true;
    let progressTimer;

    const runBootSequence = async () => {
      progressTimer = window.setInterval(() => {
        setBootProgress((current) => Math.min(current + 4, 88));
      }, 280);

      try {
        setBootMessage('Conectando con el backend...');
        await waitForRoutingBackendReady();
        if (!isMounted) return;

        setBootMessage('Cargando capas iniciales y cachés...');
        setBootProgress(96);
      } catch {
        if (isMounted) {
          setBootMessage('No se pudo validar el backend. Puedes intentarlo igualmente.');
          setBootProgress(100);
        }
      } finally {
        window.clearInterval(progressTimer);
        if (isMounted) {
          setBootProgress(100);
          window.setTimeout(() => {
            if (isMounted) {
              setAppBooting(false);
            }
          }, 420);
        }
      }
    };

    runBootSequence();
    return () => {
      isMounted = false;
      window.clearInterval(progressTimer);
    };
  }, []);

  useEffect(() => {
    const activeRequests = [];

    ['origin', 'destination'].forEach((field) => {
      if (isProgrammaticSelectionRef.current[field]) {
        isProgrammaticSelectionRef.current[field] = false;
        return;
      }

      const value = inputValues[field].trim();
      if (value.length < 3 || !suggestionOpen[field]) {
        setSuggestions((prev) => ({ ...prev, [field]: [] }));
        setSuggestionLoading((prev) => ({ ...prev, [field]: false }));
        return;
      }

      const controller = new AbortController();

      setSuggestionLoading((prev) => ({ ...prev, [field]: true }));
      const timerId = setTimeout(async () => {
        const data = await getLocationSuggestions(value, { signal: controller.signal });
        setSuggestions((prev) => ({ ...prev, [field]: data }));
        setSuggestionLoading((prev) => ({ ...prev, [field]: false }));
      }, 320);

      activeRequests.push({ controller, timerId });
    });

    return () => {
      activeRequests.forEach(({ controller, timerId }) => {
        controller.abort();
        clearTimeout(timerId);
      });
    };
  }, [inputValues, suggestionOpen]);

  const handleChange = (field, value) => {
    setInputValues((previous) => ({ ...previous, [field]: value }));
    setSuggestionOpen((prev) => ({ ...prev, [field]: true }));
    setRouteData(null);

    setSelectedPlaces((previous) => {
      const selected = previous[field];
      if (!selected) {
        return previous;
      }

      const selectedInputValue = (selected.displayText || '').trim();
      if (value.trim() === selectedInputValue) {
        return previous;
      }

      return { ...previous, [field]: null };
    });
  };

  const handleSelectSuggestion = (field, suggestion) => {
    isProgrammaticSelectionRef.current[field] = true;
    setInputValues((prev) => ({ ...prev, [field]: suggestion.displayText }));
    setSelectedPlaces((prev) => ({ ...prev, [field]: suggestion }));
    setSuggestions((prev) => ({ ...prev, [field]: [] }));
    setSuggestionOpen((prev) => ({ ...prev, [field]: false }));
    setRouteData(null);
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
      setInfoMessage(`El modo ${selectedMode.label.toLowerCase()} estará disponible en próximos slices.`);
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
        origin: {
          query: inputValues.origin.trim(),
          lat: selectedPlaces.origin?.lat,
          lon: selectedPlaces.origin?.lon ?? selectedPlaces.origin?.lng,
        },
        destination: {
          query: inputValues.destination.trim(),
          lat: selectedPlaces.destination?.lat,
          lon: selectedPlaces.destination?.lon ?? selectedPlaces.destination?.lng,
        },
        mode: selectedMode.apiMode,
      });
      setRouteData(response.data);
      setInfoMessage(`Ruta ${selectedMode.label.toLowerCase()} calculada correctamente.`);
    } catch (error) {
      setRouteData(null);
      setRouteError(error instanceof Error ? error.message : 'No fue posible calcular la ruta.');
      setInfoMessage('No se pudo completar la ruta. Revisa origen/destino e inténtalo de nuevo.');
    } finally {
      setRouteLoading(false);
    }
  };

  const handleOpenSuggestions = (field) => {
    setSuggestionOpen((prev) => ({ ...prev, [field]: true }));
  };

  const handleCloseSuggestions = (field) => {
    setSuggestionOpen((prev) => ({ ...prev, [field]: false }));
  };

  const handleCloseAllSuggestions = () => {
    setSuggestionOpen(INITIAL_SUGGESTION_OPEN);
  };

  return (
    <div className={styles.page}>
      {appBooting && (
        <div className={styles.bootOverlay} role="status" aria-live="polite">
          <div className={styles.bootCard}>
            <h2>Preparando Brisa</h2>
            <p>{bootMessage}</p>
            <div className={styles.progressTrack} aria-hidden="true">
              <div className={styles.progressBar} style={{ width: `${bootProgress}%` }} />
            </div>
            <small>{bootProgress}%</small>
          </div>
        </div>
      )}
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
              <RouteSearchForm
                inputValues={inputValues}
                onFieldChange={handleChange}
                onSubmit={handleSubmit}
                loading={routeLoading}
                suggestions={suggestions}
                suggestionLoading={suggestionLoading}
                suggestionOpen={suggestionOpen}
                onOpenSuggestions={handleOpenSuggestions}
                onCloseSuggestions={handleCloseSuggestions}
                onCloseAllSuggestions={handleCloseAllSuggestions}
                onSelectSuggestion={handleSelectSuggestion}
              />
              <RouteModeSelector selectedMode={selectedMode} onSelectMode={setSelectedMode} />
              <label className={styles.toggleLabel}>
                <input
                  type="checkbox"
                  checked={showBicimadLayer}
                  onChange={(event) => setShowBicimadLayer(event.target.checked)}
                  disabled={!bicimadLayerEnabled}
                />
                Mostrar estaciones Bicimad
              </label>
              <label className={styles.toggleLabel}>
                <input
                  type="checkbox"
                  checked={showSafetyLayer}
                  onChange={(event) => setShowSafetyLayer(event.target.checked)}
                  disabled={!safetyLayerEnabled || Boolean(safetyState.error)}
                />
                Mostrar capa de seguridad ciclista v1
              </label>
              {safetyState.error && <p className={styles.warningText}>Capa de seguridad no disponible: {safetyState.error}</p>}
              {safetySummaryEnabled && safetyState.summary && (
                <p className={styles.infoText}>
                  Índice actual: {safetyState.summary.cellCount} celdas · score medio {safetyState.summary.scoreAvg}.
                  {safetyState.summary.trafficFallbackUsed
                    ? ' Tráfico en modo fallback v1.'
                    : ' Tráfico integrado con aforos.'}
                </p>
              )}
              <p className={styles.infoText}>{infoMessage}</p>
              <RouteSummaryCard routeData={routeData} loading={routeLoading} error={routeError} statusMessage={routeData ? 'Ruta lista en mapa.' : 'Sin ruta calculada todavía.'} />
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
              showBicimadLayer={showBicimadLayer && bicimadLayerEnabled}
              routeData={routeData}
              selectedOriginPlace={selectedPlaces.origin}
              selectedDestinationPlace={selectedPlaces.destination}
              safetyGrid={safetyState.grid}
              showSafetyLayer={showSafetyLayer && safetyLayerEnabled}
              safetySummary={safetyState.summary}
            />
          ) : (
            <p>Mapa desactivado por feature flag.</p>
          )}
        </section>
      </main>
    </div>
  );
}
