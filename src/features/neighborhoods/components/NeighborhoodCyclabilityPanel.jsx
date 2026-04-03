import { useEffect, useMemo, useState } from 'react';

import styles from './NeighborhoodCyclabilityPanel.module.css';

const scoreKeys = [
  ['safetyScore', 'Seguridad'],
  ['bikeInfraScore', 'Infraestructura'],
  ['lowHostilityScore', 'Confort tráfico'],
  ['nightScore', 'Noche'],
  ['junctionScore', 'Cruces'],
  ['bicimadScore', 'Bicimad'],
];

export function NeighborhoodCyclabilityPanel({ neighborhoods, selectedNeighborhoodId, onSelectNeighborhood, comparison, onCompare }) {
  const [leftId, setLeftId] = useState('');
  const [rightId, setRightId] = useState('');

  const selected = useMemo(
    () => neighborhoods.find((item) => item.neighborhoodId === selectedNeighborhoodId) || neighborhoods[0] || null,
    [neighborhoods, selectedNeighborhoodId],
  );

  useEffect(() => {
    if (!selected && neighborhoods.length > 0) {
      onSelectNeighborhood?.(neighborhoods[0].neighborhoodId);
    }
  }, [neighborhoods, onSelectNeighborhood, selected]);

  useEffect(() => {
    if (!leftId && neighborhoods[0]) setLeftId(neighborhoods[0].neighborhoodId);
    if (!rightId && neighborhoods[1]) setRightId(neighborhoods[1].neighborhoodId);
  }, [leftId, neighborhoods, rightId]);

  return (
    <section className={styles.card}>
      <h2>Índice de ciclabilidad por barrio</h2>
      <p className={styles.copy}>
        Compara qué zonas de Madrid ofrecen una experiencia ciclista más cómoda y usable. El índice combina seguridad,
        infraestructura, tráfico, noche, cruces y acceso a Bicimad.
      </p>

      <h3>Ranking</h3>
      <div className={styles.ranking}>
        {neighborhoods.slice(0, 10).map((item) => (
          <button
            key={item.neighborhoodId}
            className={`${styles.row} ${item.neighborhoodId === selectedNeighborhoodId ? styles.activeRow : ''}`}
            onClick={() => onSelectNeighborhood?.(item.neighborhoodId)}
            type="button"
          >
            <span>
              #{item.rank} {item.name}
            </span>
            <strong>{item.cyclabilityScore}</strong>
          </button>
        ))}
      </div>

      {selected && (
        <>
          <h3>Detalle de barrio</h3>
          <div className={styles.detail}>
            <p className={styles.title}>
              {selected.name} · <span>{selected.district}</span>
            </p>
            <p className={styles.bigScore}>{selected.cyclabilityScore}/100</p>
            <p className={styles.meta}>Puesto #{selected.rank} · Percentil {selected.percentile}</p>
            <p className={styles.summary}>{selected.summary}</p>

            <div className={styles.subscores}>
              {scoreKeys.map(([key, label]) => (
                <div key={key}>
                  <span>{label}</span>
                  <div className={styles.barTrack}>
                    <div className={styles.barFill} style={{ width: `${selected[key]}%` }} />
                  </div>
                </div>
              ))}
            </div>

            <ul>
              {selected.strengths?.map((text) => (
                <li key={`s-${text}`}>✅ {text}</li>
              ))}
            </ul>
            <ul>
              {selected.weaknesses?.map((text) => (
                <li key={`w-${text}`}>⚠️ {text}</li>
              ))}
            </ul>
          </div>
        </>
      )}

      <h3>Comparador de barrios</h3>
      <div className={styles.compareControls}>
        <select value={leftId} onChange={(event) => setLeftId(event.target.value)}>
          {neighborhoods.map((item) => (
            <option key={`l-${item.neighborhoodId}`} value={item.neighborhoodId}>
              {item.name}
            </option>
          ))}
        </select>
        <select value={rightId} onChange={(event) => setRightId(event.target.value)}>
          {neighborhoods.map((item) => (
            <option key={`r-${item.neighborhoodId}`} value={item.neighborhoodId}>
              {item.name}
            </option>
          ))}
        </select>
        <button type="button" onClick={() => onCompare?.(leftId, rightId)}>
          Comparar
        </button>
      </div>

      {comparison && (
        <div className={styles.compareResult}>
          <p>
            <strong>{comparison.left.name}</strong> vs <strong>{comparison.right.name}</strong>
          </p>
          {comparison.breakdown.map((item) => (
            <p key={item.key}>
              {item.label}: {item.left} - {item.right} ({item.winner === 'tie' ? 'Empate' : item.winner === 'left' ? 'Gana izquierda' : 'Gana derecha'})
            </p>
          ))}
        </div>
      )}
    </section>
  );
}
