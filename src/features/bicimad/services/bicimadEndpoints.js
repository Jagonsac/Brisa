export const bicimadEndpoints = {
  gbfsRoot: 'https://madrid.publicbikesystem.net/customer/gbfs/v2/gbfs.json',
  stationInformation: 'https://madrid.publicbikesystem.net/customer/gbfs/v2/es/station_information',
  stationStatus: 'https://madrid.publicbikesystem.net/customer/gbfs/v2/es/station_status',
  fallbackGeoJson:
    'https://datos.emtmadrid.es/dataset/5fcc0945-2cbd-46c3-801a-6a83f4167c11/resource/105ce5df-793f-4e0a-a88e-5d3b3f024a5d/download/bikestationbicimad_geojson.geojson',
};

export const apiConfig = {
  baseUrl: import.meta.env.VITE_API_BASE_URL?.trim() || '',
};

export const bicimadRequestConfig = {
  timeoutMs: 8000,
};
