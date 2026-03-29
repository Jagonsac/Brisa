import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { MapContainer, Marker, Popup, TileLayer } from 'react-leaflet';

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

export function MapView({ selectedMode }) {
  return (
    <div className={styles.wrapper}>
      <MapContainer center={madridMapConfig.center} zoom={madridMapConfig.zoom} className={styles.map} scrollWheelZoom>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {madridMapConfig.demoMarkers.map((marker) => (
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
      </MapContainer>
    </div>
  );
}
