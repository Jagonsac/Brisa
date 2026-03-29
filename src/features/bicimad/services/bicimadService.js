import { bicimadStationsSnapshot } from '../../../mocks/bicimadStationsSnapshot';
import { normalizeGbfsStations, normalizeGeoJsonStations, normalizeSnapshotStations } from '../utils/normalizeBicimadStations';
import { bicimadEndpoints, bicimadRequestConfig } from './bicimadEndpoints';

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

export async function getBicimadStations() {
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
}
