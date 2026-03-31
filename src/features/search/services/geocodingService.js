const defaultApiBaseUrl = 'http://localhost:8000';
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim() || defaultApiBaseUrl;

export async function getLocationSuggestions(query, { signal } = {}) {
  const q = query.trim();
  if (q.length < 3) {
    return [];
  }

  const url = new URL(`${apiBaseUrl.replace(/\/$/, '')}/api/geocoding/suggest`);
  url.searchParams.set('q', q);

  try {
    const response = await fetch(url.toString(), { signal });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      return [];
    }

    return Array.isArray(payload?.data) ? payload.data : [];
  } catch {
    return [];
  }
}
