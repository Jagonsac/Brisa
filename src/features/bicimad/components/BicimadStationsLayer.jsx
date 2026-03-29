import { CircleMarker, Popup } from 'react-leaflet';

const STATION_STYLE = {
  color: '#0f5ed7',
  fillColor: '#1e88ff',
  fillOpacity: 0.75,
  radius: 5,
  weight: 1,
};

export function BicimadStationsLayer({ stations }) {
  return stations.map((station) => (
    <CircleMarker key={station.id} center={[station.lat, station.lon]} pathOptions={STATION_STYLE}>
      <Popup>
        <strong>{station.name}</strong>
        <br />
        {station.address ?? 'Dirección no disponible'}
        <br />
        {station.capacity ? `Capacidad: ${station.capacity} anclajes` : 'Capacidad no disponible'}
        <br />
        Estación Bicimad
      </Popup>
    </CircleMarker>
  ));
}
