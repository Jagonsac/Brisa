import styles from './BicimadStatusCard.module.css';

const sourceLabels = {
  'gbfs-station-information': 'GBFS station_information',
  'emt-geojson-fallback': 'Fallback oficial EMT (GeoJSON)',
  'local-snapshot-fallback': 'Snapshot local de desarrollo',
};

export function BicimadStatusCard({ loading, error, source, usedFallback, stationsCount, enabled }) {
  if (!enabled) {
    return (
      <section className={styles.card}>
        <h2>Bicimad</h2>
        <p className={styles.muted}>Capa desactivada por feature flag.</p>
      </section>
    );
  }

  const sourceLabel = sourceLabels[source] ?? 'Fuente no identificada';

  return (
    <section className={styles.card}>
      <h2>Bicimad</h2>

      {loading && <p className={styles.loading}>Cargando estaciones Bicimad…</p>}

      {!loading && error && <p className={styles.error}>No se pudo cargar Bicimad: {error}</p>}

      {!loading && !error && stationsCount === 0 && <p className={styles.muted}>No hay estaciones disponibles.</p>}

      {!loading && !error && stationsCount > 0 && (
        <>
          <p className={styles.ok}>Estaciones visibles en el mapa: {stationsCount}</p>
          <p className={styles.meta}>Fuente activa: {sourceLabel}</p>
          {usedFallback && <p className={styles.fallback}>Fallback activo para mantener la demo estable.</p>}
        </>
      )}
    </section>
  );
}
