import { useEffect, useState } from 'react';

import { getBicimadStations } from '../services/bicimadService';

const INITIAL_STATE = {
  stations: [],
  loading: true,
  error: null,
  source: null,
  usedFallback: false,
};

export function useBicimadStations({ enabled }) {
  const [state, setState] = useState(INITIAL_STATE);

  useEffect(() => {
    if (!enabled) {
      setState({ ...INITIAL_STATE, loading: false });
      return;
    }

    let isCancelled = false;

    const loadStations = async () => {
      setState((previous) => ({ ...previous, loading: true, error: null }));

      try {
        const result = await getBicimadStations();
        if (isCancelled) return;

        setState({
          stations: result.stations,
          loading: false,
          error: null,
          source: result.source,
          usedFallback: result.usedFallback,
        });
      } catch (error) {
        if (isCancelled) return;

        setState({
          stations: [],
          loading: false,
          error: error instanceof Error ? error.message : 'No se pudieron cargar estaciones Bicimad.',
          source: null,
          usedFallback: false,
        });
      }
    };

    loadStations();

    return () => {
      isCancelled = true;
    };
  }, [enabled]);

  return state;
}
