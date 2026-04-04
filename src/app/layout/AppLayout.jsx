import { useEffect, useMemo, useRef, useState } from 'react';

import { BicimadStatusCard } from '../../features/bicimad/components/BicimadStatusCard';
import { useBicimadStations } from '../../features/bicimad/hooks/useBicimadStations';
import { MapView } from '../../features/map/components/MapView';
import { NeighborhoodCyclabilityPanel } from '../../features/neighborhoods/components/NeighborhoodCyclabilityPanel';
import { useNeighborhoodCyclability } from '../../features/neighborhoods/hooks/useNeighborhoodCyclability';
import { ProjectExplainer } from '../../features/projectStatus/components/ProjectExplainer';
import { ProjectStatusPanel } from '../../features/projectStatus/components/ProjectStatusPanel';
import { RouteModeSelector } from '../../features/search/components/RouteModeSelector';
import { RouteSearchForm } from '../../features/search/components/RouteSearchForm';
import { getLocationSuggestions } from '../../features/search/services/geocodingService';
import { RouteSummaryCard } from '../../features/routing/components/RouteSummaryCard';
import { useSafetyLayer } from '../../features/safety/hooks/useSafetyLayer';
import { createRoute, waitForRoutingBackendReady } from '../../features/routing/services/routesService';
import { featureFlags } from '../../shared/config/featureFlags';
import { defaultComparisonModes, ROUTE_MODES } from '../../shared/constants/routeModes';
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

const LAYER_VISIBILITY_MODE = {
  NONE: 'none',
  SAFETY: 'safety',
  CYCLABILITY: 'cyclability',
};

const ESTIMATED_KMH_BY_MODE = {
  fastest: 18,
  safe: 14,
  balanced: 16,
  night: 13,
};

function enrichRouteWithEstimatedDuration(routeData) {
  const mode = routeData?.summary?.mode;
  const speedKmh = ESTIMATED_KMH_BY_MODE[mode] || 15;
  const distanceKm = routeData?.summary?.distanceKm || 0;
  const estimatedDurationMinutes = (distanceKm / speedKmh) * 60;

  return {
    ...routeData,
    summary: {
      ...routeData.summary,
      estimatedDurationMinutes,
    },
  };
}

export function AppLayout() {
  const [appBooting, setAppBooting] = useState(true);
  const [backendReadyForBoot, setBackendReadyForBoot] = useState(false);
  const [bootProgress, setBootProgress] = useState(8);
  const [bootMessage, setBootMessage] = useState('Inicializando motor de rutas...');
  const [inputValues, setInputValues] = useState(INITIAL_INPUT_VALUES);
  const [selectedPlaces, setSelectedPlaces] = useState(INITIAL_SELECTED_PLACES);
  const [selectedRouteMode, setSelectedRouteMode] = useState(ROUTE_MODES.FASTEST.apiMode);
  const [includeNightRoute, setIncludeNightRoute] = useState(false);
  const [useBicimadRouting, setUseBicimadRouting] = useState(false);
  const [infoMessage, setInfoMessage] = useState('Selecciona origen y destino para calcular una ruta ciclista.');
  const [routesByMode, setRoutesByMode] = useState({});
  const [routeError, setRouteError] = useState('');
  const [routeLoading, setRouteLoading] = useState(false);
  const [showBicimadLayer, setShowBicimadLayer] = useState(false);
  const [activeInsightLayer, setActiveInsightLayer] = useState(LAYER_VISIBILITY_MODE.SAFETY);
  const [selectedNeighborhoodId, setSelectedNeighborhoodId] = useState('');
  const [suggestions, setSuggestions] = useState(INITIAL_SUGGESTIONS);
  const [suggestionLoading, setSuggestionLoading] = useState(INITIAL_LOADING);
  const [suggestionOpen, setSuggestionOpen] = useState(INITIAL_SUGGESTION_OPEN);
  const isProgrammaticSelectionRef = useRef({ origin: false, destination: false });

  const bicimadLayerEnabled = featureFlags.enableBicimad && featureFlags.enableBicimadStationsLayer;
  const safetyLayerEnabled = featureFlags.enableSafetyLayer;
  const safetySummaryEnabled = featureFlags.enableSafetySummary;
  const bicimadState = useBicimadStations({ enabled: bicimadLayerEnabled });
  const safetyState = useSafetyLayer({ enabled: safetyLayerEnabled || safetySummaryEnabled });
  const cyclabilityState = useNeighborhoodCyclability({ enabled: featureFlags.enableNeighborhoodCyclability });
  const shouldPreloadCyclability = featureFlags.enableNeighborhoodCyclability;
  const cyclabilityPreloadReady = !shouldPreloadCyclability || cyclabilityState.hasResolvedInitialLoad;
  const safetyLayerAvailable = safetyLayerEnabled && !safetyState.error;
  const cyclabilityLayerAvailable = featureFlags.enableNeighborhoodCyclability && !cyclabilityState.error;
  const showSafetyLayer = activeInsightLayer === LAYER_VISIBILITY_MODE.SAFETY && safetyLayerAvailable;
  const showCyclabilityLayer =
    activeInsightLayer === LAYER_VISIBILITY_MODE.CYCLABILITY && cyclabilityLayerAvailable;

  const canSubmit = useMemo(
    () => inputValues.origin.trim().length > 0 && inputValues.destination.trim().length > 0,
    [inputValues.destination, inputValues.origin],
  );

  const selectedRoute = routesByMode[selectedRouteMode] || null;

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
          setBackendReadyForBoot(true);
          setBootProgress((current) => Math.max(current, 96));
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
    if (!backendReadyForBoot) return;

    if (!cyclabilityPreloadReady) {
      setBootMessage('Precargando índice de ciclabilidad por barrio...');
      setBootProgress((current) => Math.max(current, 96));
      return;
    }

    setBootMessage('Todo listo.');
    setBootProgress(100);
    const finishTimer = window.setTimeout(() => {
      setAppBooting(false);
    }, 420);

    return () => {
      window.clearTimeout(finishTimer);
    };
  }, [backendReadyForBoot, cyclabilityPreloadReady]);

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

  useEffect(() => {
    if (activeInsightLayer === LAYER_VISIBILITY_MODE.SAFETY && !safetyLayerAvailable) {
      setActiveInsightLayer(
        cyclabilityLayerAvailable ? LAYER_VISIBILITY_MODE.CYCLABILITY : LAYER_VISIBILITY_MODE.NONE,
      );
      return;
    }

    if (activeInsightLayer === LAYER_VISIBILITY_MODE.CYCLABILITY && !cyclabilityLayerAvailable) {
      setActiveInsightLayer(safetyLayerAvailable ? LAYER_VISIBILITY_MODE.SAFETY : LAYER_VISIBILITY_MODE.NONE);
    }
  }, [activeInsightLayer, safetyLayerAvailable, cyclabilityLayerAvailable]);

  const handleChange = (field, value) => {
    setInputValues((previous) => ({ ...previous, [field]: value }));
    setSuggestionOpen((prev) => ({ ...prev, [field]: true }));
    setRoutesByMode({});

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
    setRoutesByMode({});
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setRouteError('');

    if (!canSubmit) {
      setInfoMessage('Completa origen y destino para preparar la ruta.');
      return;
    }

    if (!featureFlags.enableRealRouting) {
      setInfoMessage('El cálculo real de rutas está desactivado por feature flag.');
      return;
    }

    const requestedModes = [...defaultComparisonModes];
    if (includeNightRoute && ROUTE_MODES.NIGHT.available) {
      requestedModes.push(ROUTE_MODES.NIGHT);
    }

    setRouteLoading(true);
    if (useBicimadRouting) {
      setInfoMessage('Calculando ruta multimodal con Bicimad...');
    } else {
      setInfoMessage(
        includeNightRoute
          ? 'Calculando rutas rápida, segura, equilibrada y nocturna...'
          : 'Calculando rutas rápida, segura y equilibrada...',
      );
    }

    try {
      const modesToRequest = useBicimadRouting
        ? [{ apiMode: selectedRouteMode }]
        : requestedModes;

      const responses = await Promise.all(
        modesToRequest.map(async (mode) => {
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
            mode: mode.apiMode,
            useBicimad: useBicimadRouting,
          });

          const enriched = response.data?.summary?.estimatedDurationMinutes
            ? response.data
            : enrichRouteWithEstimatedDuration(response.data);
          return [mode.apiMode, enriched];
        }),
      );

      const nextRoutesByMode = Object.fromEntries(responses);
      setRoutesByMode(nextRoutesByMode);

      if (!nextRoutesByMode[selectedRouteMode]) {
        setSelectedRouteMode(requestedModes[0].apiMode);
      }

      if (useBicimadRouting) {
        setInfoMessage('Listo: ruta multimodal Bicimad calculada.');
      } else {
        const hasNight = Boolean(nextRoutesByMode.night);
        setInfoMessage(
          hasNight
            ? 'Listo: compara rutas rápida, segura, equilibrada y nocturna directamente en el mapa.'
            : 'Listo: compara rutas rápida, segura y equilibrada directamente en el mapa.',
        );
      }
    } catch (error) {
      setRoutesByMode({});
      setRouteError(error instanceof Error ? error.message : 'No fue posible calcular la ruta.');
      setInfoMessage('No se pudieron calcular las rutas. Revisa origen/destino e inténtalo de nuevo.');
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

              <label className={styles.toggleLabel}>
                <input
                  type="checkbox"
                  checked={includeNightRoute}
                  onChange={(event) => setIncludeNightRoute(event.target.checked)}
                  disabled={!ROUTE_MODES.NIGHT.available}
                />
                Incluir también ruta nocturna (farolas e iluminación)
              </label>

              <RouteModeSelector
                routesByMode={routesByMode}
                selectedMode={selectedRouteMode}
                onSelectMode={setSelectedRouteMode}
                loading={routeLoading}
              />

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
                  checked={useBicimadRouting}
                  onChange={(event) => setUseBicimadRouting(event.target.checked)}
                />
                Usar Bicimad (ruta multimodal)
              </label>
              <div className={styles.layerSelectorCard}>
                <h3>Visualización principal del mapa</h3>
                <p>Elige un único índice para evitar ruido visual y comparar mejor.</p>
                <div
                  className={styles.layerSelectorGroup}
                  role="radiogroup"
                  aria-label="Seleccionar índice principal del mapa"
                >
                  <button
                    type="button"
                    role="radio"
                    aria-checked={activeInsightLayer === LAYER_VISIBILITY_MODE.SAFETY}
                    className={`${styles.layerOptionButton} ${
                      activeInsightLayer === LAYER_VISIBILITY_MODE.SAFETY ? styles.layerOptionButtonActive : ''
                    }`}
                    onClick={() => setActiveInsightLayer(LAYER_VISIBILITY_MODE.SAFETY)}
                    disabled={!safetyLayerAvailable}
                  >
                    Índice de seguridad
                  </button>
                  <button
                    type="button"
                    role="radio"
                    aria-checked={activeInsightLayer === LAYER_VISIBILITY_MODE.CYCLABILITY}
                    className={`${styles.layerOptionButton} ${
                      activeInsightLayer === LAYER_VISIBILITY_MODE.CYCLABILITY ? styles.layerOptionButtonActive : ''
                    }`}
                    onClick={() => setActiveInsightLayer(LAYER_VISIBILITY_MODE.CYCLABILITY)}
                    disabled={!cyclabilityLayerAvailable}
                  >
                    Índice de ciclabilidad
                  </button>
                  <button
                    type="button"
                    role="radio"
                    aria-checked={activeInsightLayer === LAYER_VISIBILITY_MODE.NONE}
                    className={`${styles.layerOptionButton} ${
                      activeInsightLayer === LAYER_VISIBILITY_MODE.NONE ? styles.layerOptionButtonActive : ''
                    }`}
                    onClick={() => setActiveInsightLayer(LAYER_VISIBILITY_MODE.NONE)}
                  >
                    Sin índice
                  </button>
                </div>
              </div>
              {safetyState.error && <p className={styles.warningText}>Capa de seguridad no disponible: {safetyState.error}</p>}
              {cyclabilityState.error && <p className={styles.warningText}>Índice por barrio no disponible: {cyclabilityState.error}</p>}
              {safetySummaryEnabled && safetyState.summary && (
                <p className={styles.infoText}>
                  Índice actual: {safetyState.summary.cellCount} celdas · score medio {safetyState.summary.scoreAvg}.
                  {safetyState.summary.trafficFallbackUsed
                    ? ' Tráfico en modo fallback v1.'
                    : ' Tráfico integrado con aforos.'}
                </p>
              )}
              <p className={styles.infoText}>{infoMessage}</p>
              <RouteSummaryCard
                selectedRoute={selectedRoute}
                routesByMode={routesByMode}
                selectedMode={selectedRouteMode}
                loading={routeLoading}
                error={routeError}
                statusMessage={selectedRoute ? 'Rutas listas en mapa.' : 'Sin rutas calculadas todavía.'}
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

          {featureFlags.enableNeighborhoodCyclability && (
            <NeighborhoodCyclabilityPanel
              neighborhoods={cyclabilityState.list}
              selectedNeighborhoodId={selectedNeighborhoodId}
              onSelectNeighborhood={setSelectedNeighborhoodId}
              comparison={cyclabilityState.comparison}
              onCompare={cyclabilityState.runComparison}
            />
          )}

          {featureFlags.enableProjectStatusPanel && <ProjectStatusPanel />}
        </aside>

        <section className={styles.mapContainer}>
          {featureFlags.enableMap ? (
            <MapView
              bicimadStations={bicimadState.stations}
              showBicimadLayer={showBicimadLayer && bicimadLayerEnabled}
              routesByMode={routesByMode}
              selectedRouteMode={selectedRouteMode}
              selectedOriginPlace={selectedPlaces.origin}
              selectedDestinationPlace={selectedPlaces.destination}
              safetyGrid={safetyState.grid}
              showSafetyLayer={showSafetyLayer && safetyLayerEnabled}
              safetySummary={safetyState.summary}
              cyclabilityGeojson={cyclabilityState.geojson}
              showCyclabilityLayer={showCyclabilityLayer && featureFlags.enableNeighborhoodCyclability}
              selectedNeighborhoodId={selectedNeighborhoodId}
              onSelectNeighborhood={setSelectedNeighborhoodId}
            />
          ) : (
            <p>Mapa desactivado por feature flag.</p>
          )}
        </section>
      </main>
    </div>
  );
}
