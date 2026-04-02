import { featureFlags } from '../config/featureFlags';

export const ROUTE_MODES = {
  FAST: { key: 'fast', apiMode: 'fastest', label: 'Rápida', available: true },
  SAFE: { key: 'safe', apiMode: 'safe', label: 'Segura', available: featureFlags.enableSafeRouting },
  BALANCED: { key: 'balanced', apiMode: 'balanced', label: 'Equilibrada', available: featureFlags.enableBalancedRouting },
  NIGHT: { key: 'night', apiMode: 'night', label: 'Nocturna', available: featureFlags.enableNightRouting },
};

export const routeModeOptions = [ROUTE_MODES.FAST, ROUTE_MODES.SAFE, ROUTE_MODES.BALANCED, ROUTE_MODES.NIGHT];
