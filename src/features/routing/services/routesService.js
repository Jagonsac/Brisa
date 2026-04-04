const defaultApiBaseUrl = 'http://localhost:8000';
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim() || defaultApiBaseUrl;

function buildApiUrl(path) {
  const base = apiBaseUrl.replace(/\/$/, '');
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;

  if (!base) {
    return normalizedPath;
  }

  if (/\/api$/i.test(base) && normalizedPath.startsWith('/api/')) {
    return `${base}${normalizedPath.slice(4)}`;
  }

  return `${base}${normalizedPath}`;
}


function normalizeApiError(status, payload) {
  const detail = payload?.detail;
  const detailCode = typeof detail === 'object' ? detail.code : undefined;
  const detailMessage = typeof detail === 'object' ? detail.message : undefined;

  const byCode = {
    mode_not_available: 'El modo seleccionado aún no está disponible.',
    location_not_found: detailMessage || 'No hemos podido localizar el origen o destino indicado.',
    route_not_found: 'No hemos encontrado una ruta válida entre esos puntos.',
    invalid_route_request: 'Faltan datos para calcular la ruta.',
    invalid_route_payload: detailMessage || 'El formato enviado para calcular la ruta no es válido.',
    graph_warming_up: 'La red ciclista aún se está preparando. Inténtalo de nuevo en unos segundos.',
    internal_error: 'Se produjo un error interno al calcular la ruta.',
  };

  if (detailCode && byCode[detailCode]) {
    return byCode[detailCode];
  }

  if (status >= 500) {
    return 'El backend de rutas no está disponible temporalmente.';
  }

  if (typeof detail === 'string') {
    return detail;
  }

  return detailMessage || 'No se pudo calcular la ruta con los datos indicados.';
}

const ROUTE_REQUEST_TIMEOUT_MS = 180000;
const STARTUP_CHECK_TIMEOUT_MS = 12000;

async function fetchJsonWithTimeout(url, options = {}, timeoutMs = ROUTE_REQUEST_TIMEOUT_MS) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    const payload = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(normalizeApiError(response.status, payload));
    }

    return payload;
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error('La solicitud de ruta tardó demasiado. Inténtalo de nuevo.');
    }

    if (error instanceof TypeError) {
      throw new Error('No se pudo conectar con el servicio de rutas.');
    }

    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function createRoute({ origin, destination, mode, useBicimad = false }) {
  const body = {
    origin: {
      query: origin.query,
      ...(origin.lat !== undefined && (origin.lon !== undefined || origin.lng !== undefined)
        ? { lat: origin.lat, lon: origin.lon ?? origin.lng }
        : {}),
    },
    destination: {
      query: destination.query,
      ...(destination.lat !== undefined && (destination.lon !== undefined || destination.lng !== undefined)
        ? { lat: destination.lat, lon: destination.lon ?? destination.lng }
        : {}),
    },
    mode,
    useBicimad,
  };

  return fetchJsonWithTimeout(
    buildApiUrl('/api/routes'),
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    },
    ROUTE_REQUEST_TIMEOUT_MS,
  );
}

export async function waitForRoutingBackendReady({ maxAttempts = 6 } = {}) {
  const healthUrl = buildApiUrl('/health');

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    try {
      await fetchJsonWithTimeout(healthUrl, { method: 'GET' }, STARTUP_CHECK_TIMEOUT_MS);
      return true;
    } catch (error) {
      if (attempt === maxAttempts) {
        throw error;
      }
      await new Promise((resolve) => {
        setTimeout(resolve, Math.min(1000 * attempt, 3500));
      });
    }
  }

  return false;
}
