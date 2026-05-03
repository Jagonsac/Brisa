import { useEffect, useMemo, useRef, useState } from 'react';

import { useBicimadStations } from '../../features/bicimad/hooks/useBicimadStations';
import { MapView } from '../../features/map/components/MapView';
import { useNeighborhoodCyclability } from '../../features/neighborhoods/hooks/useNeighborhoodCyclability';
import { RouteModeSelector } from '../../features/search/components/RouteModeSelector';
import { RouteSearchForm } from '../../features/search/components/RouteSearchForm';
import { getLocationSuggestions } from '../../features/search/services/geocodingService';
import { RouteSummaryCard } from '../../features/routing/components/RouteSummaryCard';
import { AiRouteInsightsPanel } from '../../features/routing/components/AiRouteInsightsPanel';
import { getAiRouteInsights } from '../../features/routing/services/aiInsightsService';
import { useSafetyLayer } from '../../features/safety/hooks/useSafetyLayer';
import { createRoute, waitForRoutingBackendReady } from '../../features/routing/services/routesService';
import { featureFlags } from '../../shared/config/featureFlags';
import { defaultComparisonModes, ROUTE_MODES } from '../../shared/constants/routeModes';
import { WelcomeModal } from './components/WelcomeModal';
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
  const [selectedRouteMode, setSelectedRouteMode] = useState(ROUTE_MODES.BALANCED.apiMode);
  const [includeNightRoute, setIncludeNightRoute] = useState(false);
  const [useBicimadRouting, setUseBicimadRouting] = useState(false);
  const [infoMessage, setInfoMessage] = useState('');
  const [routesByMode, setRoutesByMode] = useState({});
  const [routeError, setRouteError] = useState('');
  const [routeLoading, setRouteLoading] = useState(false);
  const [activeInsightLayer, setActiveInsightLayer] = useState(LAYER_VISIBILITY_MODE.SAFETY);
  const [isMobile, setIsMobile] = useState(false);
  const [selectedNeighborhoodId, setSelectedNeighborhoodId] = useState('');
  const [suggestions, setSuggestions] = useState(INITIAL_SUGGESTIONS);
  const [suggestionLoading, setSuggestionLoading] = useState(INITIAL_LOADING);
  const [suggestionOpen, setSuggestionOpen] = useState(INITIAL_SUGGESTION_OPEN);
  const [usingCurrentLocation, setUsingCurrentLocation] = useState(false);
  const [showWelcomeModal, setShowWelcomeModal] = useState(true);
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
  const hasCalculatedRoutes = Object.keys(routesByMode).length > 0;
  const [mobileControlsCollapsed, setMobileControlsCollapsed] = useState(false);
  const [aiInsights, setAiInsights] = useState(null);
  const [aiInsightsLoading, setAiInsightsLoading] = useState(false);
  const [aiInsightsError, setAiInsightsError] = useState('');
  const [aiPanelOpen, setAiPanelOpen] = useState(false);
  const [showAiHazards, setShowAiHazards] = useState(false);
  const hasActiveBicimadRoute = Boolean(useBicimadRouting && selectedRoute?.transportMode === 'bicimad');
  const showBicimadLayer = useBicimadRouting && bicimadLayerEnabled && !hasActiveBicimadRoute;

  useEffect(() => {
    const media = window.matchMedia('(max-width: 768px)');
    const handleChange = () => setIsMobile(media.matches);
    handleChange();
    media.addEventListener('change', handleChange);
    return () => media.removeEventListener('change', handleChange);
  }, []);

  useEffect(() => {
    if (!isMobile) {
      setMobileControlsCollapsed(false);
      return;
    }

    if (hasCalculatedRoutes) {
      setMobileControlsCollapsed(true);
    }
  }, [hasCalculatedRoutes, isMobile]);

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
    setAiInsights(null);
    setAiPanelOpen(false);
    setShowAiHazards(false);
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
      const modesToRequest = requestedModes;

      const settledResponses = await Promise.allSettled(
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

      const responses = [];
      const failedModes = [];

      settledResponses.forEach((result, index) => {
        if (result.status === 'fulfilled') {
          responses.push(result.value);
          return;
        }

        failedModes.push(modesToRequest[index]?.apiMode);
      });

      if (responses.length === 0) {
        throw new Error('No fue posible calcular ninguna alternativa de ruta.');
      }

      const nextRoutesByMode = Object.fromEntries(responses);
      setRoutesByMode(nextRoutesByMode);
      setActiveInsightLayer(LAYER_VISIBILITY_MODE.NONE);

      if (nextRoutesByMode[ROUTE_MODES.BALANCED.apiMode]) {
        setSelectedRouteMode(ROUTE_MODES.BALANCED.apiMode);
      } else if (!nextRoutesByMode[selectedRouteMode]) {
        const [firstAvailableMode] = Object.keys(nextRoutesByMode);
        if (firstAvailableMode) {
          setSelectedRouteMode(firstAvailableMode);
        }
      }

      if (failedModes.length > 0) {
        setRouteError(`Algunos perfiles no se pudieron calcular: ${failedModes.join(', ')}.`);
      }

      if (useBicimadRouting) {
        const hasNight = Boolean(nextRoutesByMode.night);
        setInfoMessage(
          hasNight
            ? 'Listo: compara rutas multimodales Bicimad rápida, segura, equilibrada y nocturna.'
            : 'Listo: compara rutas multimodales Bicimad rápida, segura y equilibrada.',
        );
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

  const handleUseCurrentLocation = () => {
    if (!navigator.geolocation) {
      setRouteError('Tu navegador no soporta geolocalización.');
      return;
    }

    setUsingCurrentLocation(true);
    setRouteError('');

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = Number(position.coords.latitude.toFixed(6));
        const lon = Number(position.coords.longitude.toFixed(6));
        const displayText = `Mi ubicación actual (${lat}, ${lon})`;

        isProgrammaticSelectionRef.current.origin = true;
        setInputValues((prev) => ({ ...prev, origin: displayText }));
        setSelectedPlaces((prev) => ({
          ...prev,
          origin: {
            displayText,
            label: 'Mi ubicación actual',
            lat,
            lon,
          },
        }));
        setSuggestions((prev) => ({ ...prev, origin: [] }));
        setSuggestionOpen((prev) => ({ ...prev, origin: false }));
        setRoutesByMode({});
        setInfoMessage('Origen actualizado con tu localización actual.');
        setUsingCurrentLocation(false);
      },
      (error) => {
        const message =
          error.code === error.PERMISSION_DENIED
            ? 'Permiso de ubicación denegado. No hemos podido usar tu localización actual.'
            : 'No se ha podido obtener tu localización actual. Inténtalo de nuevo.';
        setRouteError(message);
        setUsingCurrentLocation(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000,
      },
    );
  };


  const handleAnalyzeWithAi = async () => {
    setAiPanelOpen(true);
    if (aiInsights || aiInsightsLoading) return;
    setAiInsightsLoading(true);
    setAiInsightsError('');
    try {
      const data = await getAiRouteInsights(routesByMode);
      setAiInsights(data);
      setShowAiHazards(true);
    } catch (error) {
      setAiInsightsError(error instanceof Error ? error.message : 'No se pudo analizar con IA.');
    } finally {
      setAiInsightsLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      {showWelcomeModal && !appBooting && <WelcomeModal open={showWelcomeModal} onClose={() => setShowWelcomeModal(false)} />}
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
      <header className={`${styles.header} ${isMobile ? styles.mobileOnly : ''}`}>
        <h1>Brisa</h1>
        <p>Plataforma para planificar rutas ciclistas más seguras por Madrid.</p>
      </header>

      <main className={styles.mainLayout}>
        {!isMobile && <aside className={styles.sidebar}>

          {featureFlags.enableSearchUi && (
            <section className={styles.panelCard}>
              <h2>Planificador de ruta</h2>
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
                onUseCurrentLocation={handleUseCurrentLocation}
                usingCurrentLocation={usingCurrentLocation}
              />

              <div className={styles.togglesRow}>
                <label className={styles.toggleCard}>
                  <input
                    type="checkbox"
                    checked={includeNightRoute}
                    onChange={(event) => setIncludeNightRoute(event.target.checked)}
                    disabled={!ROUTE_MODES.NIGHT.available}
                  />
                  <span className={styles.toggleSwitch} aria-hidden="true" />
                  <span className={styles.toggleTextGroup}>
                    <strong>Ruta Nocturna</strong>
                    <small>Farolas e iluminación</small>
                  </span>
                </label>
                <label className={styles.toggleCard}>
                  <input
                    type="checkbox"
                    checked={useBicimadRouting}
                    onChange={(event) => setUseBicimadRouting(event.target.checked)}
                  />
                  <span className={styles.toggleSwitch} aria-hidden="true" />
                  <span className={styles.toggleTextGroup}>
                    <strong>Bicimad</strong>
                    <small>Ruta multimodal</small>
                  </span>
                </label>
              </div>

              <RouteModeSelector
                routesByMode={routesByMode}
                selectedMode={selectedRouteMode}
                onSelectMode={setSelectedRouteMode}
                loading={routeLoading}
              />
              {safetyState.error && <p className={styles.warningText}>Capa de seguridad no disponible: {safetyState.error}</p>}
              {cyclabilityState.error && <p className={styles.warningText}>Índice por barrio no disponible: {cyclabilityState.error}</p>}
              {infoMessage && <p className={styles.infoText}>{infoMessage}</p>}
              <RouteSummaryCard
                selectedRoute={selectedRoute}
                routesByMode={routesByMode}
                selectedMode={selectedRouteMode}
                loading={routeLoading}
                error={routeError}
                statusMessage={selectedRoute ? 'Rutas listas en mapa.' : 'Sin rutas calculadas todavía.'}
              />
              {hasCalculatedRoutes && (
                <AiRouteInsightsPanel
                  insights={aiInsights}
                  loading={aiInsightsLoading}
                  error={aiInsightsError}
                  onAnalyze={handleAnalyzeWithAi}
                  onClose={() => setAiPanelOpen(false)}
                  open={aiPanelOpen}
                  disabled={!hasCalculatedRoutes}
                />
              )}
            </section>
          )}

        </aside>}

        <section className={styles.mapContainer}>
          {isMobile && (
            <>
              <div className={`${styles.mobileTopOverlay} ${mobileControlsCollapsed ? styles.mobileTopOverlayCollapsed : ''}`}>
                {mobileControlsCollapsed && (
                  <button type="button" className={styles.expandMobileControlsButton} onClick={() => setMobileControlsCollapsed(false)}>
                    Calcular otra ruta
                  </button>
                )}
                {!mobileControlsCollapsed && (
                  <>
                <RouteSearchForm
                  compact={isMobile}
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
                  onUseCurrentLocation={handleUseCurrentLocation}
                  usingCurrentLocation={usingCurrentLocation}
                />
                <div className={styles.mobileToggles}>
                  <label className={styles.toggleCard}>
                    <input type="checkbox" checked={includeNightRoute} onChange={(event) => setIncludeNightRoute(event.target.checked)} disabled={!ROUTE_MODES.NIGHT.available} />
                    <span className={styles.toggleSwitch} aria-hidden="true" />
                    <span className={styles.toggleTextGroup}><strong>Ruta Nocturna</strong><small>Iluminación</small></span>
                  </label>
                  <label className={styles.toggleCard}>
                    <input type="checkbox" checked={useBicimadRouting} onChange={(event) => setUseBicimadRouting(event.target.checked)} />
                    <span className={styles.toggleSwitch} aria-hidden="true" />
                    <span className={styles.toggleTextGroup}><strong>Bicimad</strong><small>Multimodal</small></span>
                  </label>
                </div>
                </>
                )}
                {hasCalculatedRoutes && (
                <RouteModeSelector
                  routesByMode={routesByMode}
                  selectedMode={selectedRouteMode}
                  onSelectMode={setSelectedRouteMode}
                  loading={routeLoading}
                  compact
                />
                )}
              </div>
              <div className={styles.mobileBottomOverlay} role="radiogroup" aria-label="Visualización principal del mapa">
                <button type="button" className={`${styles.layerOptionButton} ${activeInsightLayer === LAYER_VISIBILITY_MODE.SAFETY ? styles.layerOptionButtonActive : ''}`} onClick={() => setActiveInsightLayer(LAYER_VISIBILITY_MODE.SAFETY)} disabled={!safetyLayerAvailable}>Seguridad</button>
                <button type="button" className={`${styles.layerOptionButton} ${activeInsightLayer === LAYER_VISIBILITY_MODE.CYCLABILITY ? styles.layerOptionButtonActive : ''}`} onClick={() => setActiveInsightLayer(LAYER_VISIBILITY_MODE.CYCLABILITY)} disabled={!cyclabilityLayerAvailable}>Ciclabilidad</button>
                <button type="button" className={`${styles.layerOptionButton} ${activeInsightLayer === LAYER_VISIBILITY_MODE.NONE ? styles.layerOptionButtonActive : ''}`} onClick={() => setActiveInsightLayer(LAYER_VISIBILITY_MODE.NONE)}>Ninguno</button>
              </div>
            </>
          )}
          {!isMobile && (
            <div className={styles.desktopMapControls} role="radiogroup" aria-label="Visualización principal del mapa">
              <button type="button" className={`${styles.layerOptionButton} ${activeInsightLayer === LAYER_VISIBILITY_MODE.SAFETY ? styles.layerOptionButtonActive : ''}`} onClick={() => setActiveInsightLayer(LAYER_VISIBILITY_MODE.SAFETY)} disabled={!safetyLayerAvailable}>Seguridad</button>
              <button type="button" className={`${styles.layerOptionButton} ${activeInsightLayer === LAYER_VISIBILITY_MODE.CYCLABILITY ? styles.layerOptionButtonActive : ''}`} onClick={() => setActiveInsightLayer(LAYER_VISIBILITY_MODE.CYCLABILITY)} disabled={!cyclabilityLayerAvailable}>Ciclabilidad</button>
              <button type="button" className={`${styles.layerOptionButton} ${activeInsightLayer === LAYER_VISIBILITY_MODE.NONE ? styles.layerOptionButtonActive : ''}`} onClick={() => setActiveInsightLayer(LAYER_VISIBILITY_MODE.NONE)}>Sin índice</button>
            </div>
          )}
          {featureFlags.enableMap ? (
            <MapView
              bicimadStations={bicimadState.stations}
              showBicimadLayer={showBicimadLayer && bicimadLayerEnabled}
              routesByMode={routesByMode}
              selectedRouteMode={selectedRouteMode}
              onSelectMode={setSelectedRouteMode}
              selectedOriginPlace={selectedPlaces.origin}
              selectedDestinationPlace={selectedPlaces.destination}
              safetyGrid={safetyState.grid}
              showSafetyLayer={showSafetyLayer && safetyLayerEnabled}
              cyclabilityGeojson={cyclabilityState.geojson}
              showCyclabilityLayer={showCyclabilityLayer && featureFlags.enableNeighborhoodCyclability}
              selectedNeighborhoodId={selectedNeighborhoodId}
              onSelectNeighborhood={setSelectedNeighborhoodId}
              loading={routeLoading}
              showAiHazards={showAiHazards}
            />
          ) : (
            <p>Mapa desactivado por feature flag.</p>
          )}
        </section>
      </main>
    </div>
  );
}
