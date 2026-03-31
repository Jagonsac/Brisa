const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim() || '';

async function fetchJsonWithTimeout(url, options = {}, timeoutMs = 30000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    const payload = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(payload?.detail || `Error HTTP ${response.status}`);
    }

    return payload;
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function createRoute({ originQuery, destinationQuery, mode }) {
  if (!apiBaseUrl) {
    throw new Error('VITE_API_BASE_URL no está configurada.');
  }

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
