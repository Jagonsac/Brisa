import { featureFlags } from '../config/featureFlags';

export const ROUTE_MODES = {
  FASTEST: {
    key: 'fastest',
    apiMode: 'fastest',
    label: 'Rápida',
    shortDescription: 'Prioriza llegar antes al destino.',
    color: '#e63946',
    available: true,
  },
  SAFE: {
    key: 'safe',
    apiMode: 'safe',
    label: 'Segura',
    shortDescription: 'Busca tramos con mejor seguridad ciclista.',
    color: '#1ea672',
    available: featureFlags.enableSafeRouting,
  },
  BALANCED: {
    key: 'balanced',
    apiMode: 'balanced',
    label: 'Equilibrada',
    shortDescription: 'Combina tiempo y seguridad.',
    color: '#f59f00',
    available: featureFlags.enableBalancedRouting,
  },
  NIGHT: {
    key: 'night',
    apiMode: 'night',
    label: 'Nocturna',
    shortDescription: 'Favorece tramos con mejor iluminación.',
    color: '#6f42c1',
    available: featureFlags.enableNightRouting,
  },
};

export const defaultComparisonModes = [ROUTE_MODES.FASTEST, ROUTE_MODES.SAFE, ROUTE_MODES.BALANCED];

export const routeModeOptions = [ROUTE_MODES.FASTEST, ROUTE_MODES.SAFE, ROUTE_MODES.BALANCED, ROUTE_MODES.NIGHT];

export const routeModeByApiMode = routeModeOptions.reduce((accumulator, mode) => {
  accumulator[mode.apiMode] = mode;
  return accumulator;
}, {});
