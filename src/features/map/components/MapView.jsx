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

export function MapView({ selectedMode, bicimadStations, showBicimadLayer, routeData }) {
  const routeFeature = routeData?.routeGeoJson ?? null;
  const originPosition = routeData ? [routeData.origin.lat, routeData.origin.lon] : null;
  const destinationPosition = routeData ? [routeData.destination.lat, routeData.destination.lon] : null;

  return (
    <div className={styles.wrapper}>
      <MapContainer center={madridMapConfig.center} zoom={madridMapConfig.zoom} className={styles.map} scrollWheelZoom>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {!routeFeature &&
          madridMapConfig.demoMarkers.map((marker) => (
            <Marker key={marker.id} position={marker.position}>
              <Popup>
                <strong>{marker.name}</strong>
                <br />
                {marker.description}
                <br />
                Modo actual: {selectedMode.label}
              </Popup>
            </Marker>
          ))}

        {routeFeature && (
          <>
            <GeoJSON data={routeFeature} style={{ color: '#1f6feb', weight: 5, opacity: 0.9 }} />
            <RouteBoundsController routeFeature={routeFeature} />
            {originPosition && (
              <Marker position={originPosition}>
                <Popup>Origen: {routeData.origin.displayName}</Popup>
              </Marker>
            )}
            {destinationPosition && (
              <Marker position={destinationPosition}>
                <Popup>Destino: {routeData.destination.displayName}</Popup>
              </Marker>
            )}
          </>
        )}

        {showBicimadLayer && bicimadStations.length > 0 && <BicimadStationsLayer stations={bicimadStations} />}
      </MapContainer>
    </div>
  );
}
