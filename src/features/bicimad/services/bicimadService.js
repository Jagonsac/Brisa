import { bicimadStationsSnapshot } from '../../../mocks/bicimadStationsSnapshot';
import { normalizeGbfsStations, normalizeGeoJsonStations, normalizeSnapshotStations } from '../utils/normalizeBicimadStations';
import { apiConfig, bicimadEndpoints, bicimadRequestConfig } from './bicimadEndpoints';

const fetchJsonWithTimeout = async (url, timeoutMs) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, { signal: controller.signal });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status} en ${url}`);
    }

    return await response.json();
  } finally {
    clearTimeout(timeoutId);
  }
};

const getStationsFromBackend = async () => {
  const endpoint = `${apiConfig.baseUrl.replace(/\/$/, '')}/api/stations`;
  const payload = await fetchJsonWithTimeout(endpoint, bicimadRequestConfig.timeoutMs);

  const stations = Array.isArray(payload?.data) ? normalizeSnapshotStations(payload.data) : [];

  if (stations.length === 0) {
    throw new Error('El backend respondió sin estaciones válidas.');
  }

  return {
    stations,
    source: payload?.meta?.source ?? 'backend-unknown',
    usedFallback: Boolean(payload?.meta?.fallbackUsed),
  };
};

const getStationsDirectlyFromProviders = async () => {
  const errors = [];

  try {
    const gbfsPayload = await fetchJsonWithTimeout(bicimadEndpoints.stationInformation, bicimadRequestConfig.timeoutMs);
    const stations = normalizeGbfsStations(gbfsPayload);
    if (stations.length > 0) {
      return {
        stations,
        source: 'gbfs-station-information',
        usedFallback: false,
      };
    }

    errors.push('GBFS no devolvió estaciones válidas.');
  } catch (error) {
    errors.push(`GBFS falló: ${error instanceof Error ? error.message : 'error desconocido'}`);
  }

  try {
    const geoJsonPayload = await fetchJsonWithTimeout(bicimadEndpoints.fallbackGeoJson, bicimadRequestConfig.timeoutMs);
    const stations = normalizeGeoJsonStations(geoJsonPayload);
    if (stations.length > 0) {
      return {
        stations,
        source: 'emt-geojson-fallback',
        usedFallback: true,
      };
    }

    errors.push('Fallback GeoJSON no devolvió estaciones válidas.');
  } catch (error) {
    errors.push(`GeoJSON oficial falló: ${error instanceof Error ? error.message : 'error desconocido'}`);
  }

  const stations = normalizeSnapshotStations(bicimadStationsSnapshot);
  if (stations.length > 0) {
    return {
      stations,
      source: 'local-snapshot-fallback',
      usedFallback: true,
      warning: errors.join(' | '),
    };
  }

  throw new Error(errors.join(' | ') || 'No fue posible cargar estaciones Bicimad.');
};

export async function getBicimadStations() {
  if (apiConfig.baseUrl) {
    try {
      return await getStationsFromBackend();
    } catch (error) {
      const fallbackResult = await getStationsDirectlyFromProviders();
      return {
        ...fallbackResult,
        warning: `Fallback frontend activo: ${error instanceof Error ? error.message : 'error desconocido'}`,
      };
    }
  }

  return getStationsDirectlyFromProviders();
}
