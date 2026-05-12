const defaultApiBaseUrl = import.meta.env.DEV ? 'http://localhost:8000' : '';
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim() || defaultApiBaseUrl;
const SAFETY_REQUEST_TIMEOUT_MS = 20000;

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
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), SAFETY_REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(buildApiUrl(path), { signal: controller.signal });
    const payload = await response.json().catch(() => ({}));

    if (!response.ok) {
      const detail = payload?.detail?.message || 'Servicio de seguridad no disponible.';
      throw new Error(detail);
    }

    return payload;
  } catch (error) {
    if (error?.name === 'AbortError') {
      throw new Error('La capa de seguridad tardó demasiado en responder.');
    }

    if (error instanceof TypeError) {
      throw new Error('No se pudo conectar con la API de seguridad.');
    }

    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

export function getSafetyGrid(aggregation = 'neighborhood') {
  return fetchJson(`/api/safety/grid?aggregation=${encodeURIComponent(aggregation)}`);
}

export function getSafetySummary() {
  return fetchJson('/api/safety/summary');
}
