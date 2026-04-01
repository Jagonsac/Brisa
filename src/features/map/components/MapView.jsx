import { useEffect } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { GeoJSON, MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet';

import { BicimadStationsLayer } from '../../bicimad/components/BicimadStationsLayer';
import { madridMapConfig } from '../../../mocks/madridMapConfig';
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

function RouteBoundsController({ routeFeature }) {
  const map = useMap();

  useEffect(() => {
    if (!routeFeature) return;
    const layer = L.geoJSON(routeFeature);
    const bounds = layer.getBounds();
    if (bounds.isValid()) {
      map.fitBounds(bounds.pad(0.15));
    }
  }, [map, routeFeature]);

  return null;
}

export function MapView({ selectedOriginPlace, selectedDestinationPlace, bicimadStations, showBicimadLayer, routeData }) {
  const routeFeature = routeData?.routeGeoJson ?? null;
  const originPoint = selectedOriginPlace || routeData?.origin || null;
  const destinationPoint = selectedDestinationPlace || routeData?.destination || null;
  const originLon = originPoint?.lon ?? originPoint?.lng;
  const destinationLon = destinationPoint?.lon ?? destinationPoint?.lng;

  const originPosition = originPoint && originLon !== undefined ? [originPoint.lat, originLon] : null;
  const destinationPosition = destinationPoint && destinationLon !== undefined ? [destinationPoint.lat, destinationLon] : null;

  return (
    <div className={styles.wrapper}>
      <MapContainer center={madridMapConfig.center} zoom={madridMapConfig.zoom} className={styles.map} scrollWheelZoom>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

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

        {routeFeature && (
          <>
            <GeoJSON data={routeFeature} style={{ color: '#1f6feb', weight: 5, opacity: 0.9 }} />
            <RouteBoundsController routeFeature={routeFeature} />
          </>
        )}

        {showBicimadLayer && bicimadStations.length > 0 && <BicimadStationsLayer stations={bicimadStations} />}
      </MapContainer>
    </div>
  );
}
