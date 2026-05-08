<script>
  import {
    analysisResults,
    isLoading,
    errorMessage,
    successMessage,
  } from '../stores/analysis.js';
  import DataPanel from './DataPanel.svelte';
  import DescriptiveView from './DescriptiveView.svelte';
  import MFDFAView from './MFDFAView.svelte';
  import SourcesView from './SourcesView.svelte';
  import ResultsTable from './ResultsTable.svelte';
  import Icon from './Icon.svelte';

  let activeTab = 'main';

  const tabs = [
    { id: 'main', label: 'Accueil', icon: 'database' },
    { id: 'descriptive', label: 'Descriptif', icon: 'chart' },
    { id: 'mfdfa', label: 'MF-DFA', icon: 'sigma' },
    { id: 'sources', label: 'Sources', icon: 'layers' },
    { id: 'comparison', label: 'Comparaison', icon: 'bar' },
  ];
</script>

<div class="app">
  <header class="topbar">
    <div class="brand">
      <div class="logo"><Icon name="sigma" size={18} /></div>
      <div class="brand-text">
        <h1>GARCH · MF-DFA — Atelier d'analyse</h1>
        <p>
          Analyse multifractale des rendements financiers — diagnostic des
          résidus GARCH/EGARCH/FIGARCH, spectre de singularité, décomposition
          de la multifractalité.
        </p>
      </div>
    </div>
    <div class="status">
      {#if $isLoading}
        <span class="status-pill loading">
          <span class="dot"></span> Calcul en cours
        </span>
      {:else if $analysisResults}
        <span class="status-pill ok">
          <Icon name="check" size={12} /> Analyse prête
        </span>
      {:else}
        <span class="status-pill idle">
          <Icon name="info" size={12} /> En attente
        </span>
      {/if}
    </div>
  </header>

  <div class="tabs" role="tablist">
    {#each tabs as tab (tab.id)}
      <button
        role="tab"
        class="tab"
        class:active={activeTab === tab.id}
        on:click={() => (activeTab = tab.id)}
      >
        <Icon name={tab.icon} size={15} />
        <span>{tab.label}</span>
      </button>
    {/each}
  </div>

  <main class="content">
    {#if activeTab === 'main'}
      <DataPanel />
    {:else if activeTab === 'descriptive'}
      <DescriptiveView />
    {:else if activeTab === 'mfdfa'}
      <MFDFAView />
    {:else if activeTab === 'sources'}
      <SourcesView />
    {:else if activeTab === 'comparison'}
      <ResultsTable />
    {/if}
  </main>

  {#if $errorMessage}
    <div class="toast error">
      <Icon name="alert" size={14} />
      <span>{$errorMessage}</span>
      <button class="toast-close" on:click={() => errorMessage.set(null)}>×</button>
    </div>
  {/if}
  {#if $successMessage}
    <div class="toast ok">
      <Icon name="check" size={14} />
      <span>{$successMessage}</span>
      <button class="toast-close" on:click={() => successMessage.set(null)}>×</button>
    </div>
  {/if}

  {#if $isLoading}
    <div class="overlay">
      <div class="overlay-card">
        <div class="spinner"></div>
        <p>Estimation des modèles et exécution du MF-DFA…</p>
      </div>
    </div>
  {/if}
</div>

<style>
  :global(html, body) {
    margin: 0;
    padding: 0;
    background: #f7f8fa;
    color: #0f172a;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    -webkit-font-smoothing: antialiased;
  }

  :global(*, *::before, *::after) { box-sizing: border-box; }

  .app {
    min-height: 100vh;
    background: #f7f8fa;
  }

  .topbar {
    background: #ffffff;
    border-bottom: 1px solid #e2e6ec;
    padding: 1.1rem 1.75rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 0.85rem;
  }

  .logo {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    background: #1d3557;
    color: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .brand-text h1 {
    margin: 0;
    font-size: 1.05rem;
    font-weight: 600;
    color: #0f172a;
    letter-spacing: -0.01em;
  }

  .brand-text p {
    margin: 0.15rem 0 0;
    color: #64748b;
    font-size: 0.8rem;
    line-height: 1.4;
    max-width: 720px;
  }

  .status-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.35rem 0.75rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 500;
    border: 1px solid transparent;
  }

  .status-pill.idle {
    background: #f1f4f8; color: #475569;
  }

  .status-pill.ok {
    background: #e6f5ee; color: #0c6e4d;
  }

  .status-pill.loading {
    background: #eef2f7; color: #1d3557;
  }

  .status-pill.loading .dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: #1d3557;
    animation: pulse 1.2s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 0.4; }
    50% { opacity: 1; }
  }

  .tabs {
    display: flex;
    gap: 0.25rem;
    padding: 0 1.5rem;
    background: #ffffff;
    border-bottom: 1px solid #e2e6ec;
    overflow-x: auto;
  }

  .tab {
    border: none;
    background: transparent;
    color: #64748b;
    padding: 0.85rem 1rem;
    font-size: 0.88rem;
    font-weight: 500;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    border-bottom: 2px solid transparent;
    transition: color 120ms ease, border-color 120ms ease;
    white-space: nowrap;
  }

  .tab:hover {
    color: #0f172a;
  }

  .tab.active {
    color: #1d3557;
    border-bottom-color: #1d3557;
  }

  .content {
    max-width: 1400px;
    margin: 0 auto;
    padding: 1.5rem;
  }

  .toast {
    position: fixed;
    bottom: 1.5rem;
    right: 1.5rem;
    background: #ffffff;
    border: 1px solid #e2e6ec;
    border-radius: 8px;
    padding: 0.75rem 0.9rem 0.75rem 0.85rem;
    display: flex;
    align-items: center;
    gap: 0.55rem;
    color: #0f172a;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
    font-size: 0.85rem;
    max-width: 420px;
    z-index: 80;
  }

  .toast.error { border-left: 3px solid #cf2a2a; color: #7a1a1a; }
  .toast.ok { border-left: 3px solid #0c6e4d; color: #0c5b3f; }

  .toast-close {
    border: none;
    background: transparent;
    color: #64748b;
    font-size: 1.1rem;
    cursor: pointer;
    line-height: 1;
    padding: 0 0.25rem;
  }

  .overlay {
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.35);
    backdrop-filter: blur(2px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 100;
  }

  .overlay-card {
    background: #ffffff;
    border-radius: 10px;
    padding: 1.5rem 1.75rem;
    display: flex;
    align-items: center;
    gap: 0.85rem;
    box-shadow: 0 12px 32px rgba(15, 23, 42, 0.18);
  }

  .overlay-card p {
    margin: 0;
    color: #0f172a;
    font-size: 0.9rem;
  }

  .spinner {
    width: 22px;
    height: 22px;
    border: 2.5px solid #e2e6ec;
    border-top-color: #1d3557;
    border-radius: 50%;
    animation: spin 0.9s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  @media (max-width: 720px) {
    .topbar {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.75rem;
      padding: 1rem 1.25rem;
    }
    .content { padding: 1rem; }
  }
</style>
