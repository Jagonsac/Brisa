const openStreetMapAttribution = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';
const cartoApiKey = import.meta.env.VITE_CARTO_BASEMAP_API_KEY?.trim();

// CARTO embeds a watermark in tiles requested without a valid basemap key.
// Keep the map usable without credentials; a configured key preserves its light style.
export const basemapConfig = cartoApiKey
  ? {
    url: `https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png?key=${encodeURIComponent(cartoApiKey)}`,
    attribution: `${openStreetMapAttribution} &copy; <a href="https://carto.com/attributions">CARTO</a>`,
    subdomains: 'abcd',
    maxNativeZoom: 20,
    maxZoom: 20,
  }
  : {
    url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: openStreetMapAttribution,
    maxNativeZoom: 19,
    maxZoom: 20,
  };
