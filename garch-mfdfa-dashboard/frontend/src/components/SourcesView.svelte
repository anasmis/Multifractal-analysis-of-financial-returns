<script>
  import { analysisResults, PALETTE } from '../stores/analysis.js';
  import Plot from './Plot.svelte';
  import Icon from './Icon.svelte';

  $: results = $analysisResults;
  $: shuffle = results?.shuffle;

  $: hqDecompTraces = shuffle
    ? [
        {
          x: shuffle.q_values,
          y: shuffle.hq_original,
          type: 'scatter',
          mode: 'lines+markers',
          name: `Original  Δh = ${shuffle.delta_h_total.toFixed(3)}`,
          line: { color: PALETTE.series.BTC, width: 2.4 },
          marker: { size: 6 },
        },
        {
          x: shuffle.q_values,
          y: shuffle.hq_shuffled,
          type: 'scatter',
          mode: 'lines+markers',
          name: `Mélangée  Δh = ${shuffle.delta_h_dist.toFixed(3)} (queues épaisses)`,
          line: { color: '#94a3b8', width: 1.6, dash: 'dash' },
          marker: { size: 5 },
        },
      ]
    : [];

  $: barTrace = shuffle
    ? [
        {
          x: ['Δh total', 'Δh corr (LRC)', 'Δh dist (queues)'],
          y: [
            shuffle.delta_h_total,
            shuffle.delta_h_corr,
            shuffle.delta_h_dist,
          ],
          type: 'bar',
          marker: {
            color: [
              PALETTE.series.BTC,
              '#5b6cff',
              '#d2691e',
            ],
            line: { width: 0 },
          },
          text: [
            shuffle.delta_h_total.toFixed(3),
            shuffle.delta_h_corr.toFixed(3),
            shuffle.delta_h_dist.toFixed(3),
          ],
          textposition: 'outside',
          hoverinfo: 'y',
        },
      ]
    : [];
</script>

{#if !results || !shuffle}
  <div class="placeholder">
    <Icon name="info" size={18} />
    <span>Lancez l'analyse pour afficher la décomposition de la multifractalité.</span>
  </div>
{:else}
  <div class="grid">
    <div class="card span-2">
      <h3>h(q) — série originale vs série mélangée</h3>
      <p class="caption">
        Le mélange détruit les corrélations longue portée mais conserve la
        distribution marginale. Le Δh résiduel provient alors uniquement des
        queues épaisses ; l'écart avec la courbe originale quantifie la
        contribution des corrélations.
      </p>
      <Plot
        traces={hqDecompTraces}
        height={340}
        layout={{
          xaxis: { title: 'q' },
          yaxis: { title: 'h(q)' },
        }}
      />
    </div>

    <div class="card">
      <h3>Décomposition de Δh</h3>
      <p class="caption">Kantelhardt (2002), Éq. 28.</p>
      <Plot
        traces={barTrace}
        height={300}
        layout={{
          yaxis: { title: 'Δh' },
          xaxis: { title: '' },
        }}
      />
    </div>

    <div class="card">
      <h3>Attribution des sources</h3>
      <div class="attr">
        <div class="attr-row">
          <span class="attr-label">Corrélations longue portée (LRC)</span>
          <span class="attr-value">{shuffle.pct_corr.toFixed(0)}%</span>
        </div>
        <div class="bar-track">
          <div
            class="bar-fill lrc"
            style="width: {Math.max(0, Math.min(100, shuffle.pct_corr))}%"
          ></div>
        </div>
        <div class="attr-row">
          <span class="attr-label">Queues épaisses</span>
          <span class="attr-value">{(100 - shuffle.pct_corr).toFixed(0)}%</span>
        </div>
        <div class="bar-track">
          <div
            class="bar-fill tails"
            style="width: {Math.max(0, Math.min(100, 100 - shuffle.pct_corr))}%"
          ></div>
        </div>
      </div>
      <p class="caption" style="margin-top: 1rem;">
        {#if shuffle.pct_corr > 50}
          Multifractalité dominée par les corrélations longue portée — la
          mémoire de la volatilité et le clustering portent l'essentiel du signal.
        {:else}
          Multifractalité dominée par les queues épaisses — les mouvements
          extrêmes structurent davantage le spectre que la persistance.
        {/if}
      </p>
    </div>
  </div>
{/if}

<style>
  .placeholder {
    background: #ffffff;
    border: 1px dashed #cbd2dc;
    border-radius: 10px;
    padding: 2rem;
    color: #64748b;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    font-size: 0.9rem;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
  }

  .card {
    background: #ffffff;
    border: 1px solid #e2e6ec;
    border-radius: 10px;
    padding: 1rem 1.25rem 1.25rem;
  }

  .card h3 {
    margin: 0;
    font-size: 0.95rem;
    font-weight: 600;
    color: #0f172a;
    letter-spacing: -0.01em;
  }

  .caption {
    margin: 0.25rem 0 0.75rem;
    color: #64748b;
    font-size: 0.8rem;
    line-height: 1.5;
  }

  .span-2 { grid-column: 1 / -1; }

  .attr { display: grid; gap: 0.4rem; }

  .attr-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.85rem;
    color: #0f172a;
  }

  .attr-label { color: #475569; }
  .attr-value { font-family: 'JetBrains Mono', monospace; font-weight: 600; }

  .bar-track {
    height: 6px;
    background: #f1f4f8;
    border-radius: 3px;
    overflow: hidden;
    margin-bottom: 0.5rem;
  }

  .bar-fill { height: 100%; border-radius: 3px; }

  .bar-fill.lrc { background: #5b6cff; }
  .bar-fill.tails { background: #d2691e; }

  @media (max-width: 900px) {
    .grid { grid-template-columns: 1fr; }
  }
</style>
