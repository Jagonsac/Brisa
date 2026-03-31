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


function normalizeSuggestion(item) {
  const label = typeof item?.label === 'string' ? item.label.trim() : '';
  const displayTextRaw = typeof item?.displayText === 'string' ? item.displayText : item?.value;
  const displayText = typeof displayTextRaw === 'string' ? displayTextRaw.trim() : '';
  const lat = Number(item?.lat);
  const lon = Number(item?.lon);

  if (!label || !displayText || Number.isNaN(lat) || Number.isNaN(lon)) {
    return null;
  }

  return {
    label,
    displayText,
    value: displayText,
    lat,
    lon,
  };
}

export async function getLocationSuggestions(query, { signal } = {}) {
  const q = query.trim();
  if (q.length < 3) {
    return [];
  }

  const url = new URL(buildApiUrl('/api/geocoding/suggest'));
  url.searchParams.set('q', q);

  try {
    const response = await fetch(url.toString(), { signal });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      return [];
    }

    const rows = Array.isArray(payload?.data) ? payload.data : [];
    return rows.map(normalizeSuggestion).filter(Boolean);
  } catch {
    return [];
  }
}
