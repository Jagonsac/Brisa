import styles from './RouteSearchForm.module.css';

function SuggestionList({ id, suggestions, onSelect }) {
  if (suggestions.length === 0) {
    return null;
  }

  return (
    <ul id={id} className={styles.suggestionList} role="listbox">
      {suggestions.map((item, index) => (
        <li key={`${item.label}-${index}`}>
          <button type="button" onClick={() => onSelect(item)} className={styles.suggestionButton}>
            {item.label}
          </button>
        </li>
      ))}
    </ul>
  );
}

export function RouteSearchForm({
  formValues,
  onFieldChange,
  onSubmit,
  loading,
  suggestions,
  suggestionLoading,
  onSelectSuggestion,
}) {
  return (
    <form className={styles.form} onSubmit={onSubmit}>
      <label htmlFor="origin">Origen</label>
      <input
        id="origin"
        name="origin"
        placeholder="Ej. Plaza de Castilla"
        type="text"
        value={formValues.origin}
        autoComplete="off"
        onChange={(event) => onFieldChange('origin', event.target.value)}
      />
      {suggestionLoading.origin && <p className={styles.suggestionState}>Buscando sugerencias...</p>}
      <SuggestionList id="origin-suggestions" suggestions={suggestions.origin} onSelect={(item) => onSelectSuggestion('origin', item)} />

      <label htmlFor="destination">Destino</label>
      <input
        id="destination"
        name="destination"
        placeholder="Ej. Matadero Madrid"
        type="text"
        value={formValues.destination}
        autoComplete="off"
        onChange={(event) => onFieldChange('destination', event.target.value)}
      />
      {suggestionLoading.destination && <p className={styles.suggestionState}>Buscando sugerencias...</p>}
      <SuggestionList
        id="destination-suggestions"
        suggestions={suggestions.destination}
        onSelect={(item) => onSelectSuggestion('destination', item)}
      />

      <button type="submit" disabled={loading}>
        {loading ? 'Calculando...' : 'Calcular ruta'}
      </button>
    </form>
  );
}
