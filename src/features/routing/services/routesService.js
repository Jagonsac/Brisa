const defaultApiBaseUrl = 'http://localhost:8000';
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim() || defaultApiBaseUrl;

function normalizeApiError(status, payload) {
  const detail = payload?.detail;
  const detailCode = typeof detail === 'object' ? detail.code : undefined;
  const detailMessage = typeof detail === 'object' ? detail.message : undefined;

  const byCode = {
    mode_not_available: 'El modo seleccionado aún no está disponible.',
    location_not_found: detailMessage || 'No hemos podido localizar el origen o destino indicado.',
    route_not_found: 'No hemos encontrado una ruta válida entre esos puntos.',
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

async function fetchJsonWithTimeout(url, options = {}, timeoutMs = 30000) {
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
      throw new Error('No se pudo conectar con el backend de rutas. Revisa que esté iniciado y CORS habilitado.');
    }

    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function createRoute({ originQuery, destinationQuery, mode }) {
  return fetchJsonWithTimeout(
    `${apiBaseUrl.replace(/\/$/, '')}/api/routes`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ originQuery, destinationQuery, mode }),
    },
    45000,
  );
}
