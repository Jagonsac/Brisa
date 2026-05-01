import { useEffect, useRef } from 'react';

import styles from './RouteSearchForm.module.css';

function SuggestionList({ id, suggestions, onSelect }) {
  if (suggestions.length === 0) {
    return null;
  }

  return (
    <ul id={id} className={styles.suggestionList} role="listbox">
      {suggestions.map((item, index) => (
        <li key={`${item.displayText || item.value || item.label}-${index}`}>
          <button
            type="button"
            onMouseDown={(event) => {
              event.preventDefault();
              onSelect(item);
            }}
            className={styles.suggestionButton}
          >
            {item.displayText || item.value || item.label}
          </button>
        </li>
      ))}
    </ul>
  );
}

export function RouteSearchForm({
  inputValues,
  onFieldChange,
  onSubmit,
  loading,
  suggestions,
  suggestionLoading,
  suggestionOpen,
  onOpenSuggestions,
  onCloseSuggestions,
  onCloseAllSuggestions,
  onSelectSuggestion,
  compact = false,
}) {
  const formRef = useRef(null);

  useEffect(() => {
    const handlePointerDownOutside = (event) => {
      if (!formRef.current?.contains(event.target)) {
        onCloseAllSuggestions();
      }
    };

    document.addEventListener('pointerdown', handlePointerDownOutside);
    return () => {
      document.removeEventListener('pointerdown', handlePointerDownOutside);
    };
  }, [onCloseAllSuggestions]);

  return (
    <form ref={formRef} className={`${styles.form} ${compact ? styles.formCompact : ''}`} onSubmit={onSubmit}>
      <label htmlFor="origin">Origen</label>
      <input
        id="origin"
        name="origin"
        placeholder="Ej. Plaza de Castilla"
        type="text"
        value={inputValues.origin}
        autoComplete="off"
        onFocus={() => onOpenSuggestions('origin')}
        onBlur={() => onCloseSuggestions('origin')}
        onChange={(event) => onFieldChange('origin', event.target.value)}
      />
      {suggestionLoading.origin && <p className={styles.suggestionState}>Buscando sugerencias...</p>}
      {suggestionOpen.origin && (
        <SuggestionList id="origin-suggestions" suggestions={suggestions.origin} onSelect={(item) => onSelectSuggestion('origin', item)} />
      )}

      <label htmlFor="destination">Destino</label>
      <input
        id="destination"
        name="destination"
        placeholder="Ej. Matadero Madrid"
        type="text"
        value={inputValues.destination}
        autoComplete="off"
        onFocus={() => onOpenSuggestions('destination')}
        onBlur={() => onCloseSuggestions('destination')}
        onChange={(event) => onFieldChange('destination', event.target.value)}
      />
      {suggestionLoading.destination && <p className={styles.suggestionState}>Buscando sugerencias...</p>}
      {suggestionOpen.destination && (
        <SuggestionList
          id="destination-suggestions"
          suggestions={suggestions.destination}
          onSelect={(item) => onSelectSuggestion('destination', item)}
        />
      )}

      <button type="submit" disabled={loading}>
        {loading ? 'Calculando rutas...' : 'Calcular rutas comparadas'}
      </button>
    </form>
  );
}
