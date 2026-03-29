const hasValidCoordinates = (lat, lon) =>
  Number.isFinite(lat) && Number.isFinite(lon) && lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180;

const toInternalStation = ({ id, name, lat, lon, address, capacity }) => {
  if (!id || !name || !hasValidCoordinates(lat, lon)) {
    return null;
  }

  const normalizedCapacity = Number.isFinite(capacity) ? capacity : null;

  return {
    id: String(id),
    name: String(name),
    lat,
    lon,
    address: address ? String(address) : null,
    capacity: normalizedCapacity,
  };
};

export function normalizeGbfsStations(payload) {
  const stations = payload?.data?.stations;

  if (!Array.isArray(stations)) {
    return [];
  }

  return stations
    .map((station) =>
      toInternalStation({
        id: station.station_id,
        name: station.name,
        lat: Number(station.lat),
        lon: Number(station.lon ?? station.lng),
        address: station.address,
        capacity: Number(station.capacity),
      }),
    )
    .filter(Boolean);
}

export function normalizeGeoJsonStations(payload) {
  const features = payload?.features;

  if (!Array.isArray(features)) {
    return [];
  }

  return features
    .map((feature) => {
      const properties = feature?.properties ?? {};
      const coordinates = feature?.geometry?.coordinates;

      return toInternalStation({
        id: properties.station_id ?? properties.id ?? properties.number,
        name: properties.name ?? properties.nombre,
        lat: Number(coordinates?.[1]),
        lon: Number(coordinates?.[0]),
        address: properties.address ?? properties.direccion,
        capacity: Number(properties.capacity ?? properties.dock_bikes),
      });
    })
    .filter(Boolean);
}

export function normalizeSnapshotStations(snapshotStations) {
  if (!Array.isArray(snapshotStations)) {
    return [];
  }

  return snapshotStations
    .map((station) =>
      toInternalStation({
        id: station.station_id ?? station.id,
        name: station.name,
        lat: Number(station.lat),
        lon: Number(station.lon),
        address: station.address,
        capacity: Number(station.capacity),
      }),
    )
    .filter(Boolean);
}
