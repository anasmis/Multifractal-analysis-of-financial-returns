<script>
  import { parameterConfig } from '../stores/analysis.js';
  import Icon from './Icon.svelte';

  const fields = [
    {
      key: 'q_min',
      label: 'q minimum',
      symbol: 'q⁻',
      hint: 'Ordre minimal du moment. Un q négatif amplifie les segments à faible fluctuation — régimes calmes.',
      step: 1,
    },
    {
      key: 'q_max',
      label: 'q maximum',
      symbol: 'q⁺',
      hint: 'Ordre maximal du moment. Un q positif amplifie les segments à forte fluctuation — régimes de crise.',
      step: 1,
    },
    {
      key: 'q_step',
      label: 'Pas de q',
      symbol: 'Δq',
      hint: 'Espacement entre deux valeurs de q. Un pas plus fin lisse davantage la courbe h(q).',
      min: 1,
    },
    {
      key: 'min_scale',
      label: 'Échelle min',
      symbol: 's_min',
      hint: 'Plus petite taille de fenêtre s. Doit être ≥ m + 2 pour que l\'ajustement polynomial local soit défini.',
      min: 5,
    },
    {
      key: 'max_scale_divisor',
      label: 'Diviseur max',
      symbol: 'N / d',
      hint: 'L\'échelle maximale vaut N divisé par cette valeur. Le choix standard est 4 — zone bien résolue.',
      min: 2,
    },
    {
      key: 'm_order',
      label: 'Ordre DFA m',
      symbol: 'm',
      hint: 'Ordre du polynôme de détrending appliqué à chaque segment. m = 1 retire les tendances linéaires, m = 2 les quadratiques, etc.',
      min: 1,
      max: 3,
    },
    {
      key: 'shuffle_iters',
      label: 'Itérations de mélange',
      symbol: 'M',
      hint: 'Nombre de permutations du test de mélange pour décomposer Δh entre corrélations longue portée et queues épaisses.',
      min: 5,
      max: 100,
    },
  ];

  function update(key, value) {
    parameterConfig.update((cfg) => ({ ...cfg, [key]: value }));
  }

  function reset() {
    parameterConfig.set({
      q_min: -5,
      q_max: 5,
      q_step: 1,
      min_scale: 10,
      max_scale_divisor: 4,
      m_order: 1,
      shuffle_iters: 20,
    });
  }
</script>

<section class="card">
  <header class="card-head">
    <div class="head-icon"><Icon name="sliders" size={18} /></div>
    <div>
      <h2>Paramètres MF-DFA</h2>
      <p>Survolez l'icône d'aide à côté de chaque champ pour une explication brève.</p>
    </div>
    <button class="reset" on:click={reset} title="Restaurer les valeurs par défaut">
      <Icon name="refresh" size={14} /> Valeurs par défaut
    </button>
  </header>

  <div class="grid">
    {#each fields as f (f.key)}
      <div class="field">
        <div class="field-head">
          <label for={f.key}>
            <span class="field-name">{f.label}</span>
            <span class="symbol">{f.symbol}</span>
          </label>
          <span class="info" title={f.hint} aria-label={f.hint}>
            <Icon name="info" size={13} />
          </span>
        </div>
        <input
          id={f.key}
          type="number"
          step={f.step ?? 1}
          min={f.min ?? undefined}
          max={f.max ?? undefined}
          value={$parameterConfig[f.key]}
          on:input={(e) => update(f.key, parseInt(e.target.value, 10))}
        />
        <p class="hint">{f.hint}</p>
      </div>
    {/each}
  </div>
</section>

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

  .card-head h2 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: #0f172a;
    letter-spacing: -0.01em;
  }

  .card-head p {
    margin: 0.25rem 0 0;
    color: #64748b;
    font-size: 0.85rem;
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

  .reset {
    margin-left: auto;
    border: 1px solid #e2e6ec;
    background: #ffffff;
    color: #475569;
    padding: 0.4rem 0.7rem;
    border-radius: 6px;
    font-size: 0.78rem;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
  }

  .reset:hover {
    border-color: #cbd2dc;
    color: #0f172a;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1rem 1.25rem;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }

  .field-head {
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }

  .field-head label {
    flex: 1;
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
    font-size: 0.85rem;
    color: #0f172a;
    font-weight: 500;
  }

  .symbol {
    font-family: 'JetBrains Mono', 'SF Mono', 'Consolas', monospace;
    font-size: 0.78rem;
    color: #1d3557;
    background: #eef2f7;
    padding: 1px 6px;
    border-radius: 4px;
    letter-spacing: 0;
  }

  .info {
    color: #94a3b8;
    cursor: help;
    display: inline-flex;
    align-items: center;
  }

  .info:hover { color: #1d3557; }

  input[type='number'] {
    width: 100%;
    padding: 0.5rem 0.7rem;
    border: 1px solid #e2e6ec;
    border-radius: 6px;
    font-size: 0.9rem;
    color: #0f172a;
    background: #ffffff;
    font-family: 'JetBrains Mono', 'SF Mono', 'Consolas', monospace;
    transition: border-color 120ms ease, box-shadow 120ms ease;
  }

  input[type='number']:focus {
    outline: none;
    border-color: #1d3557;
    box-shadow: 0 0 0 3px rgba(29, 53, 87, 0.1);
  }

  .hint {
    margin: 0;
    font-size: 0.75rem;
    color: #64748b;
    line-height: 1.5;
  }
</style>
