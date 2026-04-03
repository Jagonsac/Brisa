import { useEffect } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { GeoJSON, MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet';

import { BicimadStationsLayer } from '../../bicimad/components/BicimadStationsLayer';
import { SafetyLegend } from '../../safety/components/SafetyLegend';
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

function styleSafetyFeature(feature) {
  const score = feature?.properties?.safetyScore ?? 0;
  return {
    color: '#f8fbff',
    weight: 0.9,
    opacity: 0.7,
    fillOpacity: 0.5,
    fillColor: getSafetyColor(score),
  };
}

function styleCyclabilityFeature(feature, selectedNeighborhoodId) {
  const score = feature?.properties?.cyclabilityScore ?? 0;
  const hue = Math.round((score / 100) * 120);
  const fillColor = `hsl(${hue}, 62%, 45%)`;
  const isSelected = feature?.properties?.neighborhoodId === selectedNeighborhoodId;
  return {
    color: isSelected ? '#0f2f60' : '#f2f7ff',
    weight: isSelected ? 2.2 : 0.9,
    opacity: 0.8,
    fillOpacity: isSelected ? 0.72 : 0.56,
    fillColor,
  };
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
      hoveredLayer.setStyle({
        weight: 2.2,
        color: '#1f365f',
        opacity: 0.95,
        fillOpacity: 0.66,
      });
      hoveredLayer.bringToFront();
      hoveredLayer.openPopup(event.latlng);
    },
    mousemove: (event) => {
      layer.getPopup()?.setLatLng(event.latlng);
    },
    mouseout: () => {
      layer.closePopup();
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
  safetySummary,
  cyclabilityGeojson,
  showCyclabilityLayer,
  selectedNeighborhoodId,
  onSelectNeighborhood,
}) {
  const routeEntries = Object.entries(routesByMode);
  const routeFeatures = routeEntries
    .map(([, routeData]) => routeData?.routeGeoJson)
    .filter((feature) => Boolean(feature));

  const selectedRouteData = routesByMode[selectedRouteMode] || null;
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
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {showCyclabilityLayer && cyclabilityGeojson && (
          <GeoJSON
            data={cyclabilityGeojson}
            style={(feature) => styleCyclabilityFeature(feature, selectedNeighborhoodId)}
            onEachFeature={(feature, layer) => bindCyclabilityPopup(feature, layer, onSelectNeighborhood, selectedNeighborhoodId)}
          />
        )}

        {showSafetyLayer && safetyGrid && <GeoJSON data={safetyGrid} style={styleSafetyFeature} onEachFeature={bindSafetyPopup} />}

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

        {routeEntries.map(([modeKey, routeData]) => {
          const modeMeta = routeModeByApiMode[modeKey];
          const isActive = modeKey === selectedRouteMode;
          const routeFeature = routeData?.routeGeoJson;

          if (!routeFeature) {
            return null;
          }

          return (
            <GeoJSON
              key={modeKey}
              data={routeFeature}
              style={{
                color: modeMeta?.color || '#1f6feb',
                weight: isActive ? 6.5 : 4.25,
                opacity: isActive ? 0.98 : 0.76,
                dashArray: isActive ? undefined : '8 6',
              }}
            />
          );
        })}

        {routeFeatures.length > 0 && <RouteBoundsController routeFeatures={routeFeatures} />}

        {showBicimadLayer && bicimadStations.length > 0 && <BicimadStationsLayer stations={bicimadStations} />}
      </MapContainer>
      <SafetyLegend visible={showSafetyLayer} summary={safetySummary} />
      {showCyclabilityLayer && <div className={styles.cyclabilityLegend}>Índice ciclabilidad 0–100 (rojo→verde)</div>}
    </div>
  );
}
