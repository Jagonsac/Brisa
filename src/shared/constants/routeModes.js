export const ROUTE_MODES = {
  FAST: { key: 'fast', apiMode: 'fastest', label: 'Rápida', available: true },
  SAFE: { key: 'safe', apiMode: 'safe', label: 'Segura', available: false },
  BALANCED: { key: 'balanced', apiMode: 'balanced', label: 'Equilibrada', available: false },
  NIGHT: { key: 'night', apiMode: 'night', label: 'Nocturna', available: false },
};

export const routeModeOptions = [ROUTE_MODES.FAST, ROUTE_MODES.SAFE, ROUTE_MODES.BALANCED, ROUTE_MODES.NIGHT];
