<script>
  import { analysisResults } from '../stores/analysis.js';
  import Icon from './Icon.svelte';

  function fmt(num, digits = 3) {
    if (num === null || num === undefined || Number.isNaN(num)) return '—';
    return Number(num).toFixed(digits);
  }

  function fmtPct(num, digits = 1) {
    if (num === null || num === undefined || Number.isNaN(num)) return '—';
    return `${Number(num).toFixed(digits)}%`;
  }

  $: r = $analysisResults;
</script>

{#if r}
  <section class="card">
    <header class="card-head">
      <div class="head-icon"><Icon name="grid" size={18} /></div>
      <div>
        <h2>Métriques des modèles</h2>
        <p>AIC / BIC / log-vraisemblance et multifractalité résiduelle par modèle.</p>
      </div>
    </header>

    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Modèle</th>
            <th>AIC</th>
            <th>BIC</th>
            <th>Log-V</th>
            <th>Persistance</th>
            <th>h(2)</th>
            <th>Δh</th>
            <th>Δα</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Rendements originaux</strong></td>
            <td>—</td>
            <td>—</td>
            <td>—</td>
            <td>—</td>
            <td>{fmt(r.original_metrics.h_q2)}</td>
            <td>{fmt(r.original_metrics.delta_h)}</td>
            <td>{fmt(r.original_metrics.delta_alpha)}</td>
          </tr>
          <tr class:best={r.best_model_aic === 'GARCH'}>
            <td><strong>GARCH(1,1)-t</strong></td>
            <td>{fmt(r.garch_metrics.aic, 1)}</td>
            <td>{fmt(r.garch_metrics.bic, 1)}</td>
            <td>{fmt(r.garch_metrics.log_likelihood, 1)}</td>
            <td>{fmt(r.garch_metrics.persistence, 4)}</td>
            <td>{fmt(r.garch_metrics.h_q2)}</td>
            <td>{fmt(r.garch_metrics.delta_h)}</td>
            <td>{fmt(r.garch_metrics.delta_alpha)}</td>
          </tr>
          <tr class:best={r.best_model_aic === 'EGARCH'}>
            <td><strong>EGARCH(1,1)-t</strong></td>
            <td>{fmt(r.egarch_metrics.aic, 1)}</td>
            <td>{fmt(r.egarch_metrics.bic, 1)}</td>
            <td>{fmt(r.egarch_metrics.log_likelihood, 1)}</td>
            <td>{fmt(r.egarch_metrics.persistence, 4)}</td>
            <td>{fmt(r.egarch_metrics.h_q2)}</td>
            <td>{fmt(r.egarch_metrics.delta_h)}</td>
            <td>{fmt(r.egarch_metrics.delta_alpha)}</td>
          </tr>
          <tr class:best={r.best_model_aic === 'FIGARCH'}>
            <td><strong>FIGARCH(1,d,1)-t</strong></td>
            <td>{fmt(r.figarch_metrics.aic, 1)}</td>
            <td>{fmt(r.figarch_metrics.bic, 1)}</td>
            <td>{fmt(r.figarch_metrics.log_likelihood, 1)}</td>
            <td>{fmt(r.figarch_metrics.persistence, 4)}</td>
            <td>{fmt(r.figarch_metrics.h_q2)}</td>
            <td>{fmt(r.figarch_metrics.delta_h)}</td>
            <td>{fmt(r.figarch_metrics.delta_alpha)}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="callouts">
      <div class="callout">
        <span class="callout-label">Meilleur AIC</span>
        <span class="callout-value">{r.best_model_aic}</span>
      </div>
      <div class="callout">
        <span class="callout-label">Δh résiduel minimal</span>
        <span class="callout-value">{r.best_model_mf_reduction}</span>
      </div>
      {#if r.shuffle}
        <div class="callout">
          <span class="callout-label">Δh — part LRC</span>
          <span class="callout-value">{fmtPct(r.shuffle.pct_corr, 0)}</span>
        </div>
      {/if}
    </div>
  </section>

  <section class="card">
    <header class="card-head">
      <div class="head-icon"><Icon name="list" size={18} /></div>
      <div>
        <h2>Réduction de multifractalité par modèle</h2>
        <p>Part du Δh et du Δα originaux absorbée par chaque modèle.</p>
      </div>
    </header>

    <div class="interp-grid">
      {#each Object.entries(r.interpretation) as [model, data]}
        <div class="interp-card">
          <div class="interp-head">
            <span class="dot dot-{model.toLowerCase()}"></span>
            <h4>{model}</h4>
          </div>
          <dl>
            <div>
              <dt>Réduction de Δh</dt>
              <dd>{fmtPct(data.delta_h_reduction, 1)}</dd>
            </div>
            <div>
              <dt>Réduction de Δα</dt>
              <dd>{fmtPct(data.delta_alpha_reduction, 1)}</dd>
            </div>
          </dl>
          <div
            class="badge"
            class:warn={data.multifractal_persistent}
            class:ok={!data.multifractal_persistent}
          >
            <Icon
              name={data.multifractal_persistent ? 'alert' : 'check'}
              size={12}
            />
            {data.message}
          </div>
        </div>
      {/each}
    </div>
  </section>
{:else}
  <div class="placeholder">
    <Icon name="info" size={18} />
    <span>Lancez l'analyse pour afficher les métriques des modèles.</span>
  </div>
{/if}

<style>
  .card {
    background: #ffffff;
    border: 1px solid #e2e6ec;
    border-radius: 10px;
    padding: 1.25rem 1.5rem 1.5rem;
    margin-bottom: 1rem;
  }

  .card-head {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    margin-bottom: 1rem;
  }

  .head-icon {
    flex: 0 0 auto;
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: #eef2f7;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #1d3557;
  }

  .card-head h2 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: #0f172a;
  }

  .card-head p {
    margin: 0.25rem 0 0;
    color: #64748b;
    font-size: 0.85rem;
  }

  .table-wrapper { overflow-x: auto; }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
  }

  thead th {
    text-align: right;
    padding: 0.6rem 0.75rem;
    color: #475569;
    font-weight: 500;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    border-bottom: 1px solid #e2e6ec;
  }

  thead th:first-child { text-align: left; }

  tbody td {
    text-align: right;
    padding: 0.55rem 0.75rem;
    color: #0f172a;
    font-family: 'JetBrains Mono', 'SF Mono', 'Consolas', monospace;
    border-bottom: 1px solid #f1f4f8;
  }

  tbody td:first-child {
    text-align: left;
    font-family: 'Inter', system-ui, sans-serif;
  }

  tbody tr.best { background: #f0f6ff; }
  tbody tr.best td:first-child::before {
    content: '';
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #1d3557;
    margin-right: 0.5rem;
    vertical-align: middle;
  }

  .callouts {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 0.75rem;
    margin-top: 1rem;
  }

  .callout {
    background: #f8fafc;
    border: 1px solid #e2e6ec;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
  }

  .callout-label {
    font-size: 0.72rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .callout-value {
    font-size: 1.1rem;
    font-weight: 600;
    color: #0f172a;
    font-family: 'JetBrains Mono', monospace;
  }

  .interp-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 1rem;
  }

  .interp-card {
    border: 1px solid #e2e6ec;
    border-radius: 8px;
    padding: 0.85rem 1rem 1rem;
    background: #fbfcfe;
  }

  .interp-head { display: flex; align-items: center; gap: 0.5rem; }
  .interp-head h4 {
    margin: 0;
    font-size: 0.95rem;
    color: #0f172a;
    font-weight: 600;
  }

  .dot {
    width: 8px; height: 8px; border-radius: 50%;
  }
  .dot-garch { background: #5b6cff; }
  .dot-egarch { background: #10a37f; }
  .dot-figarch { background: #d2691e; }

  dl {
    margin: 0.75rem 0 0.75rem;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.4rem 1rem;
  }
  dl > div { display: flex; flex-direction: column; }
  dt {
    font-size: 0.72rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  dd {
    margin: 0;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
    color: #0f172a;
  }

  .badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.25rem 0.5rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 500;
  }
  .badge.warn { background: #fef3e6; color: #a3530b; }
  .badge.ok { background: #e6f5ee; color: #0c6e4d; }

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
</style>
