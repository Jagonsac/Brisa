import { useEffect, useState } from 'react';

import { getSafetyGrid, getSafetySummary } from '../services/safetyService';

export function useSafetyLayer({ enabled }) {
  const [grid, setGrid] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!enabled) return;
    let active = true;

    async function run() {
      setLoading(true);
      setError('');

      try {
        const [gridPayload, summaryPayload] = await Promise.all([getSafetyGrid(), getSafetySummary()]);
        if (!active) return;
        setGrid(gridPayload?.data ?? null);
        setSummary(summaryPayload?.data ?? null);
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : 'No se pudo cargar la capa de seguridad.');
      } finally {
        if (active) setLoading(false);
      }
    }

    run();

    return () => {
      active = false;
    };
  }, [enabled]);

  return { grid, summary, loading, error };
}
