<script>
  import { analysisResults, dataset, PALETTE } from '../stores/analysis.js';
  import Plot from './Plot.svelte';
  import Icon from './Icon.svelte';

  $: results = $analysisResults;
  $: stats = results?.descriptive;

  function fmt(x, digits = 4) {
    if (x === null || x === undefined || Number.isNaN(x)) return '—';
    return Number(x).toFixed(digits);
  }

  function fmtSci(x, digits = 2) {
    if (x === null || x === undefined || Number.isNaN(x)) return '—';
    if (Math.abs(x) >= 0.001) return Number(x).toFixed(4);
    return Number(x).toExponential(digits);
  }

  $: returns = results?.returns ?? [];
  $: dates = results?.dates ?? $dataset?.dates ?? null;
  $: prices = $dataset?.prices ?? null;

  $: priceTrace = prices && prices.length
    ? [{
        x: dates,
        y: prices,
        type: 'scatter',
        mode: 'lines',
        line: { color: PALETTE.series.BTC, width: 1.4 },
        name: 'Prix',
        hovertemplate: '%{x}<br>%{y:,.0f} USD<extra></extra>',
      }]
    : null;

  $: returnsTrace = returns.length
    ? [{
        x: dates ? dates.slice(0, returns.length) : Array.from({ length: returns.length }, (_, i) => i),
        y: returns,
        type: 'scattergl',
        mode: 'lines',
        line: { color: '#0f172a', width: 0.8 },
        name: 'Rendements log',
        hovertemplate: '%{x}<br>r = %{y:.4f}<extra></extra>',
      }]
    : null;

  $: histTrace = stats?.histogram_returns
    ? (() => {
        const h = stats.histogram_returns;
        const N = (n) => Math.exp(-0.5 * Math.pow((n - h.mean) / h.std, 2)) /
          (h.std * Math.sqrt(2 * Math.PI));
        const xs = h.centers;
        const gauss = xs.map(N);
        return [
          {
            x: xs,
            y: h.density,
            type: 'bar',
            marker: { color: '#5b6cff', opacity: 0.55, line: { width: 0 } },
            name: 'Empirique',
          },
          {
            x: xs,
            y: gauss,
            type: 'scatter',
            mode: 'lines',
            line: { color: '#d2691e', width: 2 },
            name: 'Loi normale',
          },
        ];
      })()
    : null;

  $: qqTrace = stats?.qq_plot
    ? (() => {
        const q = stats.qq_plot;
        const minX = Math.min(...q.theoretical);
        const maxX = Math.max(...q.theoretical);
        return [
          {
            x: q.theoretical,
            y: q.empirical,
            type: 'scattergl',
            mode: 'markers',
            marker: { color: '#1d3557', size: 4, opacity: 0.5 },
            name: 'Échantillon',
          },
          {
            x: [minX, maxX],
            y: [q.slope * minX + q.intercept, q.slope * maxX + q.intercept],
            type: 'scatter',
            mode: 'lines',
            line: { color: '#d2691e', width: 1.6 },
            name: 'Référence',
          },
        ];
      })()
    : null;

  $: acfSquared = stats?.acf_squared ?? [];
  $: acfAbs = stats?.acf_abs ?? [];

  $: acfSqTrace = acfSquared.length
    ? [
        {
          x: acfSquared.map((_, i) => i + 1),
          y: acfSquared,
          type: 'bar',
          marker: { color: '#5b6cff', opacity: 0.7, line: { width: 0 } },
          name: 'ACF(r²)',
        },
      ]
    : null;

  $: acfAbsTrace = acfAbs.length
    ? [
        {
          x: acfAbs.map((_, i) => i + 1),
          y: acfAbs,
          type: 'bar',
          marker: { color: '#10a37f', opacity: 0.7, line: { width: 0 } },
          name: 'ACF(|r|)',
        },
      ]
    : null;

  $: ccdf = results?.ccdf;
  $: ccdfTraces = ccdf
    ? (() => {
        const traces = [
          {
            x: ccdf.x,
            y: ccdf.y,
            type: 'scattergl',
            mode: 'markers',
            marker: { color: '#1d3557', size: 3, opacity: 0.6 },
            name: 'CCDF',
          },
        ];
        if (ccdf.fit_x && ccdf.fit_y) {
          traces.push({
            x: ccdf.fit_x,
            y: ccdf.fit_y,
            type: 'scatter',
            mode: 'lines',
            line: { color: '#d2691e', width: 1.8 },
            name: ccdf.nu_hat ? `Loi de puissance ν ≈ ${ccdf.nu_hat.toFixed(2)}` : 'Loi de puissance',
          });
        }
        return traces;
      })()
    : null;

  $: vol = results?.conditional_volatility;
  $: condVolTraces = vol
    ? [
        {
          x: dates ? dates.slice(0, vol.GARCH.length) : Array.from({ length: vol.GARCH.length }, (_, i) => i),
          y: vol.GARCH,
          type: 'scattergl',
          mode: 'lines',
          line: { color: PALETTE.series.GARCH, width: 1.0 },
          name: 'GARCH',
        },
        {
          x: dates ? dates.slice(0, vol.EGARCH.length) : Array.from({ length: vol.EGARCH.length }, (_, i) => i),
          y: vol.EGARCH,
          type: 'scattergl',
          mode: 'lines',
          line: { color: PALETTE.series.EGARCH, width: 1.0 },
          name: 'EGARCH',
        },
        {
          x: dates ? dates.slice(0, vol.FIGARCH.length) : Array.from({ length: vol.FIGARCH.length }, (_, i) => i),
          y: vol.FIGARCH,
          type: 'scattergl',
          mode: 'lines',
          line: { color: PALETTE.series.FIGARCH, width: 1.0 },
          name: 'FIGARCH',
        },
      ]
    : null;
</script>

{#if !results}
  <div class="placeholder">
    <Icon name="info" size={18} />
    <span>Lancez l'analyse pour afficher les statistiques descriptives.</span>
  </div>
{:else}
  <div class="grid kpis">
    <div class="kpi">
      <span class="kpi-label">Observations</span>
      <span class="kpi-value">{stats.n_observations}</span>
    </div>
    <div class="kpi">
      <span class="kpi-label">Moyenne</span>
      <span class="kpi-value">{fmtSci(stats.mean, 2)}</span>
    </div>
    <div class="kpi">
      <span class="kpi-label">Écart-type (jour)</span>
      <span class="kpi-value">{fmt(stats.std)}</span>
      <span class="kpi-sub">≈ {fmt(stats.annualized_vol_pct, 1)}% annualisé</span>
    </div>
    <div class="kpi">
      <span class="kpi-label">Asymétrie γ₁</span>
      <span class="kpi-value">{fmt(stats.skewness, 3)}</span>
    </div>
    <div class="kpi">
      <span class="kpi-label">Kurtosis excédentaire</span>
      <span class="kpi-value">{fmt(stats.excess_kurtosis, 2)}</span>
      <span class="kpi-sub">Gaussienne = 0</span>
    </div>
    <div class="kpi">
      <span class="kpi-label">Jarque–Bera</span>
      <span class="kpi-value">{fmt(stats.jarque_bera_stat, 1)}</span>
      <span class="kpi-sub">
        p = {fmtSci(stats.jarque_bera_pvalue, 2)} ·
        {stats.is_non_normal ? 'rejette la normalité' : 'compatible normale'}
      </span>
    </div>
    <div class="kpi">
      <span class="kpi-label">ACF(|r|) retard 1</span>
      <span class="kpi-value">{fmt(stats.acf_abs_lag1, 3)}</span>
      <span class="kpi-sub">clusters de volatilité</span>
    </div>
    <div class="kpi">
      <span class="kpi-label">% jours positifs</span>
      <span class="kpi-value">{fmt(stats.pct_positive_days, 1)}%</span>
    </div>
  </div>

  <div class="plot-grid">
    {#if priceTrace}
      <div class="card plot-card">
        <h3>Prix (échelle logarithmique)</h3>
        <Plot
          traces={priceTrace}
          height={300}
          layout={{
            yaxis: { type: 'log', title: 'Prix (USD)' },
            xaxis: { title: '' },
          }}
        />
      </div>
    {/if}

    {#if returnsTrace}
      <div class="card plot-card">
        <h3>Rendements log journaliers</h3>
        <Plot
          traces={returnsTrace}
          height={300}
          layout={{
            yaxis: { title: 'r_t' },
            xaxis: { title: '' },
          }}
        />
      </div>
    {/if}

    {#if histTrace}
      <div class="card plot-card">
        <h3>Distribution empirique vs loi normale</h3>
        <Plot
          traces={histTrace}
          height={300}
          layout={{
            barmode: 'overlay',
            xaxis: { title: 'r_t' },
            yaxis: { title: 'Densité' },
          }}
        />
      </div>
    {/if}

    {#if qqTrace}
      <div class="card plot-card">
        <h3>QQ-plot vs loi normale</h3>
        <Plot
          traces={qqTrace}
          height={300}
          layout={{
            xaxis: { title: 'Quantiles théoriques' },
            yaxis: { title: 'Quantiles empiriques' },
          }}
        />
      </div>
    {/if}

    {#if acfSqTrace}
      <div class="card plot-card">
        <h3>ACF de r² — effet ARCH</h3>
        <Plot
          traces={[
            ...acfSqTrace,
            {
              x: [1, acfSqTrace[0].x.length],
              y: [stats.acf_ci95, stats.acf_ci95],
              type: 'scatter', mode: 'lines',
              line: { color: '#cf2a2a', width: 1, dash: 'dash' },
              showlegend: false,
            },
            {
              x: [1, acfSqTrace[0].x.length],
              y: [-stats.acf_ci95, -stats.acf_ci95],
              type: 'scatter', mode: 'lines',
              line: { color: '#cf2a2a', width: 1, dash: 'dash' },
              showlegend: false,
            },
          ]}
          height={300}
          layout={{
            xaxis: { title: 'Retard (jours)' },
            yaxis: { title: 'Autocorrélation' },
          }}
        />
      </div>
    {/if}

    {#if acfAbsTrace}
      <div class="card plot-card">
        <h3>ACF de |r| — mémoire longue de la volatilité</h3>
        <Plot
          traces={[
            ...acfAbsTrace,
            {
              x: [1, acfAbsTrace[0].x.length],
              y: [stats.acf_ci95, stats.acf_ci95],
              type: 'scatter', mode: 'lines',
              line: { color: '#cf2a2a', width: 1, dash: 'dash' },
              showlegend: false,
            },
            {
              x: [1, acfAbsTrace[0].x.length],
              y: [-stats.acf_ci95, -stats.acf_ci95],
              type: 'scatter', mode: 'lines',
              line: { color: '#cf2a2a', width: 1, dash: 'dash' },
              showlegend: false,
            },
          ]}
          height={300}
          layout={{
            xaxis: { title: 'Retard (jours)' },
            yaxis: { title: 'Autocorrélation' },
          }}
        />
      </div>
    {/if}

    {#if ccdfTraces}
      <div class="card plot-card">
        <h3>Queues épaisses — CCDF (log–log)</h3>
        <Plot
          traces={ccdfTraces}
          height={300}
          layout={{
            xaxis: { title: '|r|', type: 'log' },
            yaxis: { title: 'P(|r| > x)', type: 'log' },
          }}
        />
      </div>
    {/if}

    {#if condVolTraces}
      <div class="card plot-card span-2">
        <h3>Volatilité conditionnelle — GARCH / EGARCH / FIGARCH</h3>
        <Plot
          traces={condVolTraces}
          height={320}
          layout={{
            yaxis: { title: 'σ̂_t (%)' },
            xaxis: { title: '' },
          }}
        />
      </div>
    {/if}
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

  .grid.kpis {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 0.75rem;
    margin-bottom: 1rem;
  }

  .kpi {
    background: #ffffff;
    border: 1px solid #e2e6ec;
    border-radius: 10px;
    padding: 0.85rem 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
  }

  .kpi-label {
    font-size: 0.75rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .kpi-value {
    font-size: 1.25rem;
    font-weight: 600;
    color: #0f172a;
    font-family: 'JetBrains Mono', 'SF Mono', 'Consolas', monospace;
  }

  .kpi-sub {
    font-size: 0.72rem;
    color: #94a3b8;
  }

  .plot-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
    gap: 1rem;
  }

  .card {
    background: #ffffff;
    border: 1px solid #e2e6ec;
    border-radius: 10px;
    padding: 1rem 1.25rem 1.25rem;
  }

  .plot-card h3 {
    margin: 0 0 0.5rem;
    font-size: 0.9rem;
    font-weight: 600;
    color: #0f172a;
    letter-spacing: -0.01em;
  }

  .span-2 { grid-column: 1 / -1; }
</style>
