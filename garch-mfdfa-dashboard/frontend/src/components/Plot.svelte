<script>
  import { onMount, onDestroy } from 'svelte';

  export let traces = [];
  export let layout = {};
  export let height = 360;
  export let config = {};

  let container;
  let Plotly;
  let mounted = false;

  const baseLayout = {
    margin: { l: 60, r: 24, t: 16, b: 50 },
    paper_bgcolor: '#ffffff',
    plot_bgcolor: '#ffffff',
    font: {
      family: 'Inter, -apple-system, "Segoe UI", system-ui, sans-serif',
      size: 12,
      color: '#1f2937',
    },
    xaxis: {
      gridcolor: '#eef1f5',
      zerolinecolor: '#cfd6df',
      linecolor: '#cfd6df',
      tickcolor: '#cfd6df',
      tickfont: { size: 11, color: '#475569' },
      titlefont: { size: 12, color: '#334155' },
    },
    yaxis: {
      gridcolor: '#eef1f5',
      zerolinecolor: '#cfd6df',
      linecolor: '#cfd6df',
      tickcolor: '#cfd6df',
      tickfont: { size: 11, color: '#475569' },
      titlefont: { size: 12, color: '#334155' },
    },
    legend: {
      orientation: 'h',
      x: 0,
      y: 1.12,
      bgcolor: 'rgba(0,0,0,0)',
      font: { size: 11, color: '#334155' },
    },
    hoverlabel: {
      bgcolor: '#0f172a',
      bordercolor: '#0f172a',
      font: { color: '#ffffff', size: 11 },
    },
  };

  const baseConfig = {
    displaylogo: false,
    responsive: true,
    modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d'],
  };

  function deepMerge(target, source) {
    const out = { ...target };
    for (const key in source) {
      if (
        source[key] &&
        typeof source[key] === 'object' &&
        !Array.isArray(source[key])
      ) {
        out[key] = deepMerge(target[key] || {}, source[key]);
      } else {
        out[key] = source[key];
      }
    }
    return out;
  }

  async function render() {
    if (!Plotly || !container) return;
    const fullLayout = deepMerge(baseLayout, layout);
    fullLayout.height = height;
    Plotly.react(container, traces, fullLayout, { ...baseConfig, ...config });
  }

  onMount(async () => {
    const mod = await import('plotly.js-dist-min');
    Plotly = mod.default || mod;
    mounted = true;
    render();
  });

  onDestroy(() => {
    if (Plotly && container) {
      try { Plotly.purge(container); } catch (_) {}
    }
  });

  $: if (mounted && container && (traces || layout)) render();
</script>

<div class="plot" bind:this={container} style="height: {height}px;"></div>

<style>
  .plot {
    width: 100%;
    min-height: 200px;
  }
</style>
