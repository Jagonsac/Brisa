import styles from './RouteSearchForm.module.css';

export function RouteSearchForm({ formValues, onFieldChange, onSubmit }) {
  return (
    <form className={styles.form} onSubmit={onSubmit}>
      <label htmlFor="origin">Origen</label>
      <input
        id="origin"
        name="origin"
        placeholder="Ej. Plaza de Castilla"
        type="text"
        value={formValues.origin}
        onChange={(event) => onFieldChange('origin', event.target.value)}
      />

      <label htmlFor="destination">Destino</label>
      <input
        id="destination"
        name="destination"
        placeholder="Ej. Matadero Madrid"
        type="text"
        value={formValues.destination}
        onChange={(event) => onFieldChange('destination', event.target.value)}
      />

      <button type="submit">Preparar ruta</button>
    </form>
  );
}
