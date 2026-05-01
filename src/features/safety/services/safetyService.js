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
    const detail = payload?.detail?.message || 'Servicio de seguridad no disponible.';
    throw new Error(detail);
  }

  return payload;
}

const CACHE_TTL_MS = 5 * 60 * 1000;
const responseCache = new Map();

function getCachedOrFetch(key, fetcher) {
  const now = Date.now();
  const cached = responseCache.get(key);

  if (cached && now - cached.timestamp < CACHE_TTL_MS) {
    return cached.promise;
  }

  const promise = fetcher().catch((error) => {
    responseCache.delete(key);
    throw error;
  });

  responseCache.set(key, { timestamp: now, promise });
  return promise;
}

export function getSafetyGrid(aggregation = 'neighborhood') {
  const key = `safety-grid:${aggregation}`;
  return getCachedOrFetch(key, () => fetchJson(`/api/safety/grid?aggregation=${encodeURIComponent(aggregation)}`));
}

export function getSafetySummary() {
  return getCachedOrFetch('safety-summary', () => fetchJson('/api/safety/summary'));
}
