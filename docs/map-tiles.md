# Map tiles

Brisa's basemap is independent of its route graph and municipal scoring layers.

## Why the hosted map showed “API KEY REQUIRED”

The previous `MapView` requested `light_all` raster tiles from CARTO without a key. CARTO now serves unauthenticated raster requests with a watermark embedded in the image. It can be a valid image response, so an ordinary tile-load error handler does not detect it.

Sources: [CARTO's official raster integration guide](https://github.com/CartoDB/basemap-styles#1-web-raster-basemaps) and [basemap key instructions](https://www.carto.com/basemaps/apikey/index.html).

## Default: OpenStreetMap

Without `VITE_CARTO_BASEMAP_API_KEY`, Brisa uses:

```text
https://tile.openstreetmap.org/{z}/{x}/{y}.png
```

This requires no API key. Visible OpenStreetMap attribution remains on the map. Native tiles stop at zoom 19; Leaflet can display them at zoom 20 by scaling. The layer uses ordinary browser caching and requests tiles for the interactive view; do not add bulk download or offline prefetching. Browser requests must keep a valid Referer. This is a best-effort community service; check the [OSMF tile policy](https://operations.osmfoundation.org/policies/tiles/) and use a suitable provider or self-hosting if usage grows.

## Optional: keep the CARTO light style

1. Obtain a basemap key from [CARTO](https://www.carto.com/basemaps/apikey/index.html). The project owner should complete the request and accept the applicable terms.
2. In local `.env`, or in Vercel's project environment variables for the intended deployment environments, set `VITE_CARTO_BASEMAP_API_KEY` to that key.
3. Rebuild/redeploy the frontend. Vite reads these values at build time; editing the hosting variable alone does not update an existing deployment.
4. Confirm that tile requests include `?key=...` and that new tiles render without the watermark. A previously cached tile may require a refresh.

A basemap key used by the browser is visible in tile requests and the built frontend. Use a dedicated basemap key with CARTO's available website restrictions, including the production domain and any intended preview/local domains. Never use an OpenAI key or other server secret here. Do not commit a real key; `.env.example` contains an empty placeholder.

When configured, Brisa uses CARTO Positron (`light_all`) with both CARTO and OpenStreetMap attribution. A missing key selects OpenStreetMap at build time; an invalid supplied key can still produce a CARTO watermark and is not silently retried against another provider.

This change affects only background tiles, attribution, and native tile zoom. Route calculations, scores, overlays, and the backend are unchanged.
