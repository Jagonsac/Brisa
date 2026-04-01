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

export function getSafetyGrid(aggregation = 'neighborhood') {
  return fetchJson(`/api/safety/grid?aggregation=${encodeURIComponent(aggregation)}`);
}

export function getSafetySummary() {
  return fetchJson('/api/safety/summary');
}
