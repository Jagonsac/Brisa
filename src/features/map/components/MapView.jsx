import { useEffect } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { GeoJSON, MapContainer, Marker, Pane, Popup, TileLayer, useMap } from 'react-leaflet';

import { BicimadStationsLayer } from '../../bicimad/components/BicimadStationsLayer';
import { getSafetyColor } from '../../safety/utils/safetyColors';
import { madridMapConfig } from '../../../mocks/madridMapConfig';
import { routeModeByApiMode } from '../../../shared/constants/routeModes';
import styles from './MapView.module.css';

import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

const originIcon = L.divIcon({ className: styles.originMarker, html: '<span>O</span>', iconSize: [24, 24], iconAnchor: [12, 12] });
const destinationIcon = L.divIcon({
  className: styles.destinationMarker,
  html: '<span>D</span>',
  iconSize: [24, 24],
  iconAnchor: [12, 12],
});
const bicimadStationIcon = L.divIcon({
  className: styles.bicimadRecommendationMarker,
  html: '<span>B</span>',
  iconSize: [24, 24],
  iconAnchor: [12, 12],
});

function RouteBoundsController({ routeFeatures }) {
  const map = useMap();

  useEffect(() => {
    if (routeFeatures.length === 0) return;

    const featureCollection = {
      type: 'FeatureCollection',
      features: routeFeatures,
    };

    const layer = L.geoJSON(featureCollection);
    const bounds = layer.getBounds();
    if (bounds.isValid()) {
      map.fitBounds(bounds.pad(0.15));
    }
  }, [map, routeFeatures]);

  return null;
}

function styleSafetyFeature(feature, soften = false) {
  const score = feature?.properties?.safetyScore ?? 0;
  return {
    color: '#f8fbff',
    weight: 0.9,
    opacity: 0.7,
    fillOpacity: soften ? 0.32 : 0.5,
    fillColor: getSafetyColor(score),
  };
}

function styleCyclabilityFeature(feature, selectedNeighborhoodId, soften = false) {
  const score = feature?.properties?.cyclabilityScore ?? 0;
  const hue = Math.round((score / 100) * 120);
  const fillColor = `hsl(${hue}, 62%, 45%)`;
  const isSelected = feature?.properties?.neighborhoodId === selectedNeighborhoodId;
  return {
    color: isSelected ? '#0f2f60' : '#f2f7ff',
    weight: isSelected ? 2.2 : 0.9,
    opacity: 0.8,
    fillOpacity: soften ? (isSelected ? 0.48 : 0.34) : (isSelected ? 0.72 : 0.56),
    fillColor,
  };
}

function darkenHexColor(hexColor, factor = 0.2) {
  const normalized = hexColor?.replace('#', '');
  if (!normalized || (normalized.length !== 3 && normalized.length !== 6)) return '#2f4b78';

  const expanded =
    normalized.length === 3
      ? normalized
          .split('')
          .map((char) => `${char}${char}`)
          .join('')
      : normalized;

  const [r, g, b] = [0, 2, 4].map((start) => parseInt(expanded.slice(start, start + 2), 16));
  const clamp = (value) => Math.max(0, Math.min(255, Math.round(value * (1 - factor))));
  return `rgb(${clamp(r)}, ${clamp(g)}, ${clamp(b)})`;
}

function bindSafetyPopup(feature, layer) {
  const properties = feature?.properties ?? {};
  const explanation = Array.isArray(properties.explanation) ? properties.explanation.join('<br/>') : '';
  const title = properties.name ? `Barrio: ${properties.name}` : `Seguridad: ${properties.safetyScore ?? '-'} / 100`;
  const accidentsLabel = properties.name ? 'Accidentes (agregado)' : 'Accidentes';
  const cellsInfo = properties.cellCount ? `<br/>Celdas agregadas: ${properties.cellCount}` : '';
  const popupContent =
    `<strong>${title}</strong><br/>Score seguridad: ${properties.safetyScore ?? '-'} / 100<br/>${accidentsLabel}: ${
      properties.accidentCount ?? 0
    }${cellsInfo}<br/>${explanation}`;

  layer.bindPopup(popupContent, { closeButton: false, autoPan: false, className: styles.safetyPopup });

  layer.on({
    mouseover: (event) => {
      const hoveredLayer = event.target;
      const baseStyle = styleSafetyFeature(feature);

      hoveredLayer.setStyle({
        ...baseStyle,
        weight: 1.8,
        color: darkenHexColor(baseStyle.fillColor, 0.18),
        opacity: 0.9,
        fillOpacity: 0.62,
      });
      const layerElement = hoveredLayer.getElement();
      layerElement?.classList.add(styles.liftedNeighborhood);
      hoveredLayer.bringToFront();
      hoveredLayer.openPopup(event.latlng);
    },
    mousemove: (event) => {
      layer.getPopup()?.setLatLng(event.latlng);
    },
    mouseout: () => {
      layer.closePopup();
      layer.getElement()?.classList.remove(styles.liftedNeighborhood);
      layer.setStyle(styleSafetyFeature(feature));
    },
    click: (event) => {
      layer.openPopup(event.latlng);
    },
  });
}

function bindCyclabilityPopup(feature, layer, onSelectNeighborhood, selectedNeighborhoodId) {
  const properties = feature?.properties ?? {};
  const popupContent = `<strong>${properties.neighborhoodName ?? 'Barrio'}</strong><br/>Índice ciclabilidad: ${
    properties.cyclabilityScore ?? '-'
  } / 100<br/>Distrito: ${properties.districtName ?? '-'}`;
  layer.bindPopup(popupContent, { className: styles.safetyPopup });

  layer.on({
    mouseover: (event) => {
      event.target.setStyle(styleCyclabilityFeature(feature, selectedNeighborhoodId));
      event.target.bringToFront();
      event.target.openPopup(event.latlng);
    },
    mouseout: () => {
      layer.closePopup();
      layer.setStyle(styleCyclabilityFeature(feature, selectedNeighborhoodId));
    },
    click: (event) => {
      onSelectNeighborhood?.(properties.neighborhoodId);
      layer.openPopup(event.latlng);
    },
  });
}

export function MapView({
  selectedOriginPlace,
  selectedDestinationPlace,
  bicimadStations,
  showBicimadLayer,
  routesByMode,
  selectedRouteMode,
  safetyGrid,
  showSafetyLayer,
  cyclabilityGeojson,
  showCyclabilityLayer,
  selectedNeighborhoodId,
  onSelectNeighborhood,
  loading = false,
}) {
  const routeEntries = Object.entries(routesByMode);
  const routeFeatures = routeEntries
    .flatMap(([, routeData]) => {
      if (Array.isArray(routeData?.segments)) {
        return routeData.segments.map((segment) => ({
          type: 'Feature',
          geometry: segment.geometry,
          properties: { segmentType: segment.type, mode: routeData?.bikeProfile || selectedRouteMode },
        }));
      }
      return [routeData?.routeGeoJson];
    })
    .filter((feature) => Boolean(feature));

  const selectedRouteData = routesByMode[selectedRouteMode] || null;
  const hasRoutes = routeEntries.length > 0;
  const originPoint = selectedOriginPlace || selectedRouteData?.origin || routeEntries[0]?.[1]?.origin || null;
  const destinationPoint = selectedDestinationPlace || selectedRouteData?.destination || routeEntries[0]?.[1]?.destination || null;
  const originLon = originPoint?.lon ?? originPoint?.lng;
  const destinationLon = destinationPoint?.lon ?? destinationPoint?.lng;

  const originPosition = originPoint && originLon !== undefined ? [originPoint.lat, originLon] : null;
  const destinationPosition = destinationPoint && destinationLon !== undefined ? [destinationPoint.lat, destinationLon] : null;

  return (
    <div className={styles.wrapper}>
      {showSafetyLayer && safetyGrid && (
        <div className={styles.hoverHint}>
          <strong>Tip:</strong> pasa el cursor por un barrio para ver su detalle de seguridad.
        </div>
      )}
      <MapContainer center={madridMapConfig.center} zoom={madridMapConfig.zoom} className={styles.map} scrollWheelZoom>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        />

        <Pane name="routes-inactive" style={{ zIndex: 430 }} />
        <Pane name="routes-active" style={{ zIndex: 470 }} />

        {showCyclabilityLayer && cyclabilityGeojson && (
          <GeoJSON
            data={cyclabilityGeojson}
            style={(feature) => styleCyclabilityFeature(feature, selectedNeighborhoodId, hasRoutes)}
            onEachFeature={(feature, layer) => bindCyclabilityPopup(feature, layer, onSelectNeighborhood, selectedNeighborhoodId)}
          />
        )}

        {showSafetyLayer && safetyGrid && <GeoJSON data={safetyGrid} style={(feature) => styleSafetyFeature(feature, hasRoutes)} onEachFeature={bindSafetyPopup} />}

        {originPosition && (
          <Marker position={originPosition} icon={originIcon}>
            <Popup>Origen: {originPoint.label || originPoint.displayName || originPoint.query}</Popup>
          </Marker>
        )}

        {destinationPosition && (
          <Marker position={destinationPosition} icon={destinationIcon}>
            <Popup>Destino: {destinationPoint.label || destinationPoint.displayName || destinationPoint.query}</Popup>
          </Marker>
        )}

        {[...routeEntries]
          .sort(([modeA], [modeB]) => {
            if (modeA === selectedRouteMode) return 1;
            if (modeB === selectedRouteMode) return -1;
            return 0;
          })
          .map(([modeKey, routeData]) => {
            const modeMeta = routeModeByApiMode[modeKey];
            const isActive = modeKey === selectedRouteMode;
            if (Array.isArray(routeData?.segments) && modeKey === selectedRouteMode) {
              return routeData.segments.map((segment, index) => (
                <GeoJSON
                  key={`${modeKey}-${segment.type}-${index}`}
                  pane="routes-active"
                  data={{ type: 'Feature', geometry: segment.geometry, properties: {} }}
                  style={{
                    color: segment.type === 'walk' ? '#2f6bff' : modeMeta?.color || '#1f6feb',
                    weight: segment.type === 'walk' ? 4.6 : 7,
                    opacity: segment.type === 'walk' ? 0.9 : 1,
                    dashArray: segment.type === 'walk' ? '6 10' : undefined,
                  }}
                />
              ));
            }

            const routeFeature = routeData?.routeGeoJson;
            if (!routeFeature) return null;
            return (
              <GeoJSON
                key={modeKey}
                pane={isActive ? 'routes-active' : 'routes-inactive'}
                data={routeFeature}
                style={{
                  color: modeMeta?.color || '#1f6feb',
                  weight: isActive ? 7 : 4,
                  opacity: isActive ? 1 : 0.64,
                  dashArray: isActive ? undefined : '8 6',
                }}
              />
            );
          })}

        {selectedRouteData?.stations?.departure && (
          <Marker position={[selectedRouteData.stations.departure.lat, selectedRouteData.stations.departure.lon]} icon={bicimadStationIcon}>
            <Popup>Salida Bicimad: {selectedRouteData.stations.departure.name}</Popup>
          </Marker>
        )}
        {selectedRouteData?.stations?.arrival && (
          <Marker position={[selectedRouteData.stations.arrival.lat, selectedRouteData.stations.arrival.lon]} icon={bicimadStationIcon}>
            <Popup>Llegada Bicimad: {selectedRouteData.stations.arrival.name}</Popup>
          </Marker>
        )}

        {routeFeatures.length > 0 && <RouteBoundsController routeFeatures={routeFeatures} />}

        {showBicimadLayer && bicimadStations.length > 0 && <BicimadStationsLayer stations={bicimadStations} />}
      </MapContainer>
      {loading && (
        <div className={styles.loadingOverlay} role="status" aria-live="polite" aria-label="Calculando rutas">
          <div className={styles.loadingCard}>
            <span className={styles.loadingSpinner} aria-hidden="true" />
            <p>Calculando rutas…</p>
          </div>
        </div>
      )}
      {showCyclabilityLayer && <div className={styles.cyclabilityLegend}>Índice ciclabilidad 0–100 (rojo→verde)</div>}
    </div>
  );
}
