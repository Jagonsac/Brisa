import { useCallback, useEffect, useState } from 'react';

import {
  compareNeighborhoods,
  getNeighborhoodCyclabilityGeojson,
  getNeighborhoodCyclabilityList,
} from '../services/cyclabilityService';

export function useNeighborhoodCyclability({ enabled }) {
  const [list, setList] = useState([]);
  const [geojson, setGeojson] = useState(null);
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(false);
  const [hasResolvedInitialLoad, setHasResolvedInitialLoad] = useState(!enabled);
  const [error, setError] = useState('');
  const [comparison, setComparison] = useState(null);

  useEffect(() => {
    if (!enabled) {
      setHasResolvedInitialLoad(true);
      return;
    }
    let active = true;
    setHasResolvedInitialLoad(false);

    async function run() {
      setLoading(true);
      setError('');

      try {
        const [listPayload, geoPayload] = await Promise.all([getNeighborhoodCyclabilityList(), getNeighborhoodCyclabilityGeojson()]);
        if (!active) return;
        setList(Array.isArray(listPayload?.data) ? listPayload.data : []);
        setGeojson(geoPayload?.data ?? null);
        setMeta(listPayload?.meta ?? null);
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : 'No se pudo cargar el índice por barrio.');
      } finally {
        if (active) {
          setLoading(false);
          setHasResolvedInitialLoad(true);
        }
      }
    }

    run();

    return () => {
      active = false;
    };
  }, [enabled]);

  const runComparison = useCallback(async (left, right) => {
    if (!left || !right) {
      setComparison(null);
      return;
    }

    const payload = await compareNeighborhoods(left, right);
    setComparison(payload?.data ?? null);
  }, []);

  return { list, geojson, meta, loading, hasResolvedInitialLoad, error, comparison, runComparison };
}
