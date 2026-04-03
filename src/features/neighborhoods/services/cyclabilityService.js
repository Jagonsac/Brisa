const defaultApiBaseUrl = 'http://localhost:8000';
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim() || defaultApiBaseUrl;

function buildApiUrl(path) {
  const base = apiBaseUrl.replace(/\/$/, '');
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;

  if (!base) return normalizedPath;
  if (/\/api$/i.test(base) && normalizedPath.startsWith('/api/')) {
    return `${base}${normalizedPath.slice(4)}`;
  }

  return `${base}${normalizedPath}`;
}

async function fetchJson(path) {
  const response = await fetch(buildApiUrl(path));
  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    const detail = payload?.detail?.message || 'No se pudo cargar ciclabilidad por barrio.';
    throw new Error(detail);
  }

  return payload;
}

export function getNeighborhoodCyclabilityList() {
  return fetchJson('/api/cyclability/neighborhoods');
}

export function getNeighborhoodCyclabilityGeojson() {
  return fetchJson('/api/cyclability/neighborhoods/geojson');
}

export function compareNeighborhoods(left, right) {
  return fetchJson(`/api/cyclability/neighborhoods/compare?left=${encodeURIComponent(left)}&right=${encodeURIComponent(right)}`);
}
