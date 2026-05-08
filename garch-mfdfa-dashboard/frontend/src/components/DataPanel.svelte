<script>
  import axios from 'axios';
  import {
    analysisResults,
    isLoading,
    errorMessage,
    successMessage,
    parameterConfig,
    dataset,
  } from '../stores/analysis.js';
  import Icon from './Icon.svelte';
  import ParameterPanel from './ParameterPanel.svelte';

  const API_URL = 'http://localhost:8000';

  let fileInput;
  let fileName = '';
  let source = 'btc';
  let btcLoaded = false;

  async function loadBtc() {
    try {
      isLoading.set(true);
      errorMessage.set(null);
      successMessage.set(null);

      const { data } = await axios.get(`${API_URL}/btc-data`);
      dataset.set(data);
      btcLoaded = true;
      successMessage.set(
        `Série BTC/USD chargée — ${data.n_observations} observations.`
      );
    } catch (err) {
      errorMessage.set(`Erreur : ${err.response?.data?.detail || err.message}`);
    } finally {
      isLoading.set(false);
    }
  }

  async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    fileName = file.name;

    const formData = new FormData();
    formData.append('file', file);

    try {
      isLoading.set(true);
      errorMessage.set(null);
      successMessage.set(null);

      const { data } = await axios.post(`${API_URL}/upload`, formData);
      dataset.set(data);
      successMessage.set(
        `${data.n_observations} observations chargées depuis ${file.name}.`
      );
    } catch (err) {
      errorMessage.set(`Erreur : ${err.response?.data?.detail || err.message}`);
    } finally {
      isLoading.set(false);
    }
  }

  async function runAnalysis() {
    const ds = $dataset;
    if (!ds || !ds.returns || ds.returns.length === 0) {
      errorMessage.set('Chargez un jeu de données avant de lancer l\'analyse.');
      return;
    }
    try {
      isLoading.set(true);
      errorMessage.set(null);
      successMessage.set(null);

      const payload = {
        returns: ds.returns,
        date_index: ds.dates || null,
        model_type: 'all',
      };
      const { data } = await axios.post(`${API_URL}/analyze`, payload, {
        params: $parameterConfig,
      });
      analysisResults.set(data);
      successMessage.set('Analyse terminée.');
    } catch (err) {
      errorMessage.set(`Erreur : ${err.response?.data?.detail || err.message}`);
    } finally {
      isLoading.set(false);
    }
  }
</script>

<section class="card">
  <header class="card-head">
    <div class="head-icon"><Icon name="database" size={18} /></div>
    <div>
      <h2>Source des données</h2>
      <p>Choisissez la série BTC/USD intégrée ou importez votre propre CSV de rendements.</p>
    </div>
  </header>

  <div class="source-toggle" role="tablist">
    <button
      role="tab"
      class="seg"
      class:active={source === 'btc'}
      on:click={() => (source = 'btc')}
    >
      Intégrée : BTC/USD
    </button>
    <button
      role="tab"
      class="seg"
      class:active={source === 'upload'}
      on:click={() => (source = 'upload')}
    >
      Importer un CSV
    </button>
  </div>

  {#if source === 'btc'}
    <div class="block">
      <p class="block-help">
        Rendements logarithmiques journaliers du Bitcoin/USD sur 2017–2024
        (≈ 2 920 observations), déjà nettoyés. La série est livrée avec le
        backend.
      </p>
      <button class="btn btn-primary" on:click={loadBtc} disabled={$isLoading}>
        <Icon name="download" size={15} />
        Charger la série BTC/USD
      </button>
    </div>
  {:else}
    <div class="block">
      <p class="block-help">
        Le CSV doit contenir une colonne <code>returns</code>,
        <code>log_returns</code> ou <code>rendement</code>. Une colonne
        <code>date</code> facultative améliore l'étiquetage temporel.
      </p>
      <label class="file-drop">
        <Icon name="upload" size={18} />
        <span>{fileName || 'Choisir un fichier CSV'}</span>
        <input
          type="file"
          accept=".csv"
          bind:this={fileInput}
          on:change={handleFileUpload}
        />
      </label>
    </div>
  {/if}

  {#if $dataset}
    <div class="ds-summary">
      <div class="ds-row">
        <span class="ds-label">Série</span>
        <span class="ds-value">{$dataset.name || 'Jeu de données personnalisé'}</span>
      </div>
      <div class="ds-row">
        <span class="ds-label">Observations</span>
        <span class="ds-value">{$dataset.n_observations}</span>
      </div>
      {#if $dataset.dates && $dataset.dates.length}
        <div class="ds-row">
          <span class="ds-label">Période</span>
          <span class="ds-value">
            {$dataset.dates[0]} → {$dataset.dates[$dataset.dates.length - 1]}
          </span>
        </div>
      {/if}
    </div>
  {/if}
</section>

<ParameterPanel />

<section class="card run-card">
  <header class="card-head">
    <div class="head-icon"><Icon name="play" size={18} /></div>
    <div>
      <h2>Lancer l'analyse</h2>
      <p>Estime GARCH / EGARCH / FIGARCH et applique le MF-DFA aux rendements et aux résidus.</p>
    </div>
  </header>
  <button
    class="btn btn-primary btn-run"
    on:click={runAnalysis}
    disabled={$isLoading || !$dataset}
  >
    <Icon name="activity" size={16} />
    {$isLoading ? 'Calcul en cours…' : 'Exécuter le pipeline complet'}
  </button>
  <p class="run-help">
    Le pipeline complet enchaîne les statistiques descriptives, l'estimation
    GARCH/EGARCH/FIGARCH, le MF-DFA sur les rendements et les résidus
    standardisés, le test de mélange et les références théoriques.
  </p>
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
    letter-spacing: -0.01em;
  }

  .card-head p {
    margin: 0.25rem 0 0;
    color: #64748b;
    font-size: 0.85rem;
    line-height: 1.4;
  }

  .source-toggle {
    display: inline-flex;
    background: #f1f4f8;
    padding: 4px;
    border-radius: 8px;
    gap: 4px;
    margin-bottom: 1rem;
  }

  .seg {
    border: none;
    background: transparent;
    color: #475569;
    padding: 0.5rem 0.9rem;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 120ms ease;
  }

  .seg:hover { color: #0f172a; }

  .seg.active {
    background: #ffffff;
    color: #0f172a;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
  }

  .block { display: flex; flex-direction: column; gap: 0.75rem; }

  .block-help {
    margin: 0;
    color: #475569;
    font-size: 0.85rem;
    line-height: 1.5;
  }

  .block-help code {
    background: #f1f4f8;
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 0.78rem;
    color: #1d3557;
  }

  .btn {
    border: 1px solid #1d3557;
    background: #1d3557;
    color: #ffffff;
    padding: 0.55rem 1rem;
    border-radius: 6px;
    font-size: 0.88rem;
    font-weight: 500;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    transition: all 120ms ease;
  }

  .btn:hover:not(:disabled) {
    background: #0f1f3d;
    border-color: #0f1f3d;
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-run { width: 100%; justify-content: center; padding: 0.75rem 1rem; }

  .file-drop {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.85rem 1rem;
    border: 1px dashed #cbd2dc;
    background: #f8fafc;
    border-radius: 8px;
    cursor: pointer;
    color: #475569;
    font-size: 0.88rem;
    transition: all 120ms ease;
  }

  .file-drop:hover {
    border-color: #1d3557;
    background: #eef2f7;
    color: #0f172a;
  }

  .file-drop input { display: none; }

  .ds-summary {
    margin-top: 1rem;
    padding: 0.85rem 1rem;
    background: #f8fafc;
    border: 1px solid #e2e6ec;
    border-radius: 8px;
    display: grid;
    gap: 0.4rem;
  }

  .ds-row { display: flex; justify-content: space-between; font-size: 0.85rem; }

  .ds-label { color: #64748b; }
  .ds-value { color: #0f172a; font-weight: 500; }

  .run-card { margin-top: 1rem; }

  .run-help {
    margin: 0.75rem 0 0;
    color: #64748b;
    font-size: 0.8rem;
    line-height: 1.5;
  }
</style>
