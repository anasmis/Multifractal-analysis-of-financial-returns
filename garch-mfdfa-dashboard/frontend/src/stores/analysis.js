import { writable } from 'svelte/store';

export const analysisResults = writable(null);

export const isLoading = writable(false);

export const errorMessage = writable(null);

export const successMessage = writable(null);

export const dataset = writable(null);

export const selectedModels = writable({
  garch: true,
  egarch: true,
  figarch: true,
});

export const parameterConfig = writable({
  q_min: -5,
  q_max: 5,
  q_step: 1,
  min_scale: 10,
  max_scale_divisor: 4,
  m_order: 1,
  shuffle_iters: 20,
});

export const PALETTE = {
  bg: '#f7f8fa',
  card: '#ffffff',
  border: '#e2e6ec',
  borderStrong: '#cbd2dc',
  text: '#0f172a',
  muted: '#64748b',
  accent: '#1d3557',
  accentSoft: '#eef2f7',
  series: {
    BTC: '#d4a017',
    ORIGINAL: '#0f172a',
    GARCH: '#5b6cff',
    EGARCH: '#10a37f',
    FIGARCH: '#d2691e',
    SHUFFLE: '#94a3b8',
    REF: '#94a3b8',
  },
};
