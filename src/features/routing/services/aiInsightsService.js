const defaultApiBaseUrl = 'http://localhost:8000';
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim() || defaultApiBaseUrl;

function buildApiUrl(path) {
  const base = apiBaseUrl.replace(/\/$/, '');
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  if (/\/api$/i.test(base) && normalizedPath.startsWith('/api/')) return `${base}${normalizedPath.slice(4)}`;
  return `${base}${normalizedPath}`;
}

export async function getAiRouteInsights(routesByMode) {
  const routes = Object.entries(routesByMode).map(([mode, route]) => ({
    mode,
    distanceKm: route?.summary?.distanceKm,
    relativeSafety: route?.summary?.relativeSafety,
    lightingQuality: route?.summary?.lightingQuality,
    nightRisk: route?.summary?.nightRisk,
    hazardPoints: route?.hazardPoints || [],
    explanations: route?.explanations || [],
  }));

  const response = await fetch(buildApiUrl('/api/ai/route-insights'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ routes }),
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload?.detail?.message || 'No se pudo generar insights IA.');
  return payload.data;
}
