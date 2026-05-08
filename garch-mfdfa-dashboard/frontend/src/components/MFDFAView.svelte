<script>
  import { analysisResults, PALETTE } from '../stores/analysis.js';
  import Plot from './Plot.svelte';
  import Icon from './Icon.svelte';

  $: results = $analysisResults;
  $: orig = results?.original_mfdfa;
  $: q = orig?.q_values ?? [];

  $: hqTraces = results
    ? [
        {
          x: q,
          y: results.original_mfdfa.hq,
          type: 'scatter',
          mode: 'lines+markers',
          name: `Original  Δh = ${results.original_metrics.delta_h.toFixed(3)}`,
          line: { color: PALETTE.series.BTC, width: 2.4 },
          marker: { size: 6 },
        },
        {
          x: q,
          y: results.garch_mfdfa.hq,
          type: 'scatter',
          mode: 'lines+markers',
          name: `Résidus GARCH  Δh = ${results.garch_metrics.delta_h.toFixed(3)}`,
          line: { color: PALETTE.series.GARCH, width: 1.6, dash: 'dash' },
          marker: { size: 5 },
        },
        {
          x: q,
          y: results.egarch_mfdfa.hq,
          type: 'scatter',
          mode: 'lines+markers',
          name: `Résidus EGARCH  Δh = ${results.egarch_metrics.delta_h.toFixed(3)}`,
          line: { color: PALETTE.series.EGARCH, width: 1.6, dash: 'dash' },
          marker: { size: 5 },
        },
        {
          x: q,
          y: results.figarch_mfdfa.hq,
          type: 'scatter',
          mode: 'lines+markers',
          name: `Résidus FIGARCH  Δh = ${results.figarch_metrics.delta_h.toFixed(3)}`,
          line: { color: PALETTE.series.FIGARCH, width: 1.6, dash: 'dash' },
          marker: { size: 5 },
        },
        {
          x: [q[0], q[q.length - 1]],
          y: [0.5, 0.5],
          type: 'scatter',
          mode: 'lines',
          name: 'h = 0.5 (bruit blanc)',
          line: { color: '#94a3b8', width: 1, dash: 'dot' },
          showlegend: true,
        },
      ]
    : [];

  $: refTraces = results?.references
    ? [
        {
          x: q,
          y: results.original_mfdfa.hq,
          type: 'scatter',
          mode: 'lines+markers',
          name: `Original Δh = ${results.original_metrics.delta_h.toFixed(3)}`,
          line: { color: PALETTE.series.BTC, width: 2.4 },
          marker: { size: 6 },
        },
        {
          x: q,
          y: results.references.white_noise.hq,
          type: 'scatter',
          mode: 'lines+markers',
          name: 'Bruit blanc (h ≈ 0,5)',
          line: { color: '#94a3b8', width: 1.4, dash: 'dash' },
          marker: { size: 4 },
        },
        {
          x: q,
          y: results.references.fbm.hq,
          type: 'scatter',
          mode: 'lines+markers',
          name: 'fBm H = 0,75 (monofractal)',
          line: { color: PALETTE.series.EGARCH, width: 1.4, dash: 'dash' },
          marker: { size: 4 },
        },
        {
          x: q,
          y: results.references.binomial_cascade.hq,
          type: 'scatter',
          mode: 'lines+markers',
          name: 'Cascade binomiale (multifractal)',
          line: { color: '#5b6cff', width: 1.4, dash: 'dash' },
          marker: { size: 4 },
        },
      ]
    : [];

  $: tauTraces = results
    ? [
        {
          x: q,
          y: results.original_mfdfa.tau_q,
          type: 'scatter',
          mode: 'lines+markers',
          name: 'τ(q) original',
          line: { color: PALETTE.series.BTC, width: 2 },
          marker: { size: 5 },
        },
        {
          x: q,
          y: q.map((qi) => qi * results.original_metrics.h_q2 - 1),
          type: 'scatter',
          mode: 'lines',
          name: `Monofractal H = ${results.original_metrics.h_q2.toFixed(3)}`,
          line: { color: '#94a3b8', width: 1.2, dash: 'dash' },
        },
      ]
    : [];

  $: falphaTraces = results
    ? [
        {
          x: results.original_mfdfa.alpha,
          y: results.original_mfdfa.falpha,
          type: 'scatter',
          mode: 'lines+markers',
          name: `Original Δα = ${results.original_metrics.delta_alpha.toFixed(3)}`,
          line: { color: PALETTE.series.BTC, width: 2.2 },
          marker: { size: 6 },
        },
        {
          x: results.garch_mfdfa.alpha,
          y: results.garch_mfdfa.falpha,
          type: 'scatter',
          mode: 'lines+markers',
          name: `GARCH Δα = ${results.garch_metrics.delta_alpha.toFixed(3)}`,
          line: { color: PALETTE.series.GARCH, width: 1.4, dash: 'dash' },
          marker: { size: 4 },
        },
        {
          x: results.egarch_mfdfa.alpha,
          y: results.egarch_mfdfa.falpha,
          type: 'scatter',
          mode: 'lines+markers',
          name: `EGARCH Δα = ${results.egarch_metrics.delta_alpha.toFixed(3)}`,
          line: { color: PALETTE.series.EGARCH, width: 1.4, dash: 'dash' },
          marker: { size: 4 },
        },
        {
          x: results.figarch_mfdfa.alpha,
          y: results.figarch_mfdfa.falpha,
          type: 'scatter',
          mode: 'lines+markers',
          name: `FIGARCH Δα = ${results.figarch_metrics.delta_alpha.toFixed(3)}`,
          line: { color: PALETTE.series.FIGARCH, width: 1.4, dash: 'dash' },
          marker: { size: 4 },
        },
      ]
    : [];
</script>

{#if !results}
  <div class="placeholder">
    <Icon name="info" size={18} />
    <span>Lancez l'analyse pour afficher les spectres multifractals.</span>
  </div>
{:else}
  <div class="grid">
    <div class="card span-2">
      <h3>h(q) — Hurst généralisé, avant/après filtrage GARCH</h3>
      <p class="caption">
        Une courbe h(q) décroissante traduit la multifractalité. Les résidus
        d'un modèle de la famille GARCH qui en absorbe la structure
        devraient s'aplatir autour de h ≈ 0,5.
      </p>
      <Plot
        traces={hqTraces}
        height={360}
        layout={{
          xaxis: { title: 'q' },
          yaxis: { title: 'h(q)' },
        }}
      />
    </div>

    <div class="card">
      <h3>Références théoriques</h3>
      <p class="caption">Comparaison avec des références mono- et multifractales générées à la volée.</p>
      <Plot
        traces={refTraces}
        height={320}
        layout={{ xaxis: { title: 'q' }, yaxis: { title: 'h(q)' } }}
      />
    </div>

    <div class="card">
      <h3>τ(q) — exposant de masse</h3>
      <p class="caption">La non-linéarité de τ(q) signe la multifractalité.</p>
      <Plot
        traces={tauTraces}
        height={320}
        layout={{ xaxis: { title: 'q' }, yaxis: { title: 'τ(q) = q·h(q) − 1' } }}
      />
    </div>

    <div class="card span-2">
      <h3>f(α) — spectre de singularité</h3>
      <p class="caption">
        La contraction du spectre après filtrage mesure la part de
        multifractalité absorbée par le modèle de la famille GARCH.
      </p>
      <Plot
        traces={falphaTraces}
        height={360}
        layout={{
          xaxis: { title: 'α (exposant de Hölder)' },
          yaxis: { title: 'f(α)' },
        }}
      />
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

  @media (max-width: 900px) {
    .grid { grid-template-columns: 1fr; }
  }
</style>
