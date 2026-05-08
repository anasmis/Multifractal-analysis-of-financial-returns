# Analyse multifractale BTC/USD — GARCH · MF-DFA

Étude empirique de la dynamique des rendements journaliers du Bitcoin
(BTC/USD, 2017–2024) combinant une famille de modèles **GARCH / EGARCH /
FIGARCH** avec l'**Analyse multifractale par fluctuations détrendées
(MF-DFA)** de Kantelhardt et al. (2002).

Le dépôt regroupe deux briques :

- `TimeSeries And Forecasting/` — pipeline scientifique en Python (récupération
  Yahoo Finance, statistiques descriptives, MF-DFA, comparaison GARCH).
- `garch-mfdfa-dashboard/` — atelier web interactif (FastAPI + Svelte +
  Plotly) qui réplique l'ensemble du pipeline et expose les résultats sous
  forme de tableaux de bord.

---

## 1. Problématique

Les rendements financiers ne se résument pas à de la volatilité changeante :
ils présentent simultanément
- un **clustering de volatilité** (mémoire longue dans les amplitudes),
- des **queues épaisses** non gaussiennes,
- une dépendance **multi-échelle** des fluctuations (multifractalité).

L'objectif est double :

1. **Caractériser** la multifractalité de la série BTC à l'aide du MF-DFA
   (exposants généralisés `h(q)`, spectre de singularité `f(α)`).
2. **Mesurer** ce que les modèles GARCH (variance conditionnelle scalaire)
   parviennent à absorber, en relançant le MF-DFA sur les **résidus
   standardisés** ẑₜ = εₜ / σ̂ₜ.

---

## 2. Données

- Source : `yfinance`, ticker **`BTC-USD`**, fréquence journalière.
- Période : **2017-01-01 → 2024-12-31** (≈ 2 920 observations exploitables
  après nettoyage).
- Variable d'analyse : rendements logarithmiques rₜ = ln(Pₜ) − ln(Pₜ₋₁).
- Fichiers générés : `btc_prix.csv`, `btc_rendements.csv`.

![Prix BTC/USD journaliers](TimeSeries%20And%20Forecasting/btc_prix.png)

---

## 3. Statistiques descriptives

Les rendements affichent les stylized facts attendus :

| Statistique             | Valeur indicative |
|-------------------------|-------------------|
| Moyenne journalière     | ≈ 1 × 10⁻³        |
| Écart-type journalier   | ≈ 3,8 % (≈ 60 % annualisé) |
| Asymétrie γ₁            | légèrement négative |
| Kurtosis excédentaire   | > 7 (queues épaisses) |
| Jarque–Bera             | rejette fortement la normalité (p ≪ 10⁻³) |
| ACF(|r|) lag 1          | ≈ 0,30 (clusters de volatilité) |

La figure ci-dessous regroupe la chronique des rendements, la distribution
empirique vs gaussienne, le QQ-plot et l'autocorrélogramme de r².

![Analyse descriptive BTC](TimeSeries%20And%20Forecasting/btc_analyse_descriptive.png)

> **Lecture** : la distribution s'écarte nettement d'une loi normale ; les
> autocorrélations significatives de |r| et r² confirment l'effet ARCH et
> motivent une modélisation à variance conditionnelle.

---

## 4. MF-DFA — Multifractal Detrended Fluctuation Analysis

### 4.1 Validation sur séries de référence

Avant d'appliquer le MF-DFA au BTC, le pipeline est validé sur trois
références théoriques :

- **Bruit blanc gaussien** : `h(q) ≈ 0,5 ∀q`, Δh ≈ 0 — pas de mémoire.
- **fBm** (H = 0,75) : `h(q) ≈ H ∀q`, Δh ≈ 0 — monofractal persistant.
- **Cascade binomiale** (a = 0,6) : `h(q)` strictement décroissant — multifractal.

![MF-DFA bruit blanc](TimeSeries%20And%20Forecasting/mfdfa_whitenoise.png)
![MF-DFA cascade multifractale](TimeSeries%20And%20Forecasting/mfdfa_multifractal.png)
![Comparaison h(q) — mono vs multifractal](TimeSeries%20And%20Forecasting/mfdfa_comparison.png)

Le spectre de singularité `f(α)` de la cascade donne une largeur Δα non nulle
caractéristique d'un signal multifractal.

![Spectre f(α) — cascade](TimeSeries%20And%20Forecasting/mfdfa_falpha.png)

### 4.2 Application BTC/USD

Sur la série BTC réelle :

| Métrique          | Valeur estimée | Interprétation |
|-------------------|----------------|----------------|
| h(2)              | ≈ 0,56         | persistance LRC modérée |
| Δh = h(q⁻) − h(q⁺)| ≈ 0,29         | multifractalité significative |
| Δα                | ≈ 0,56         | spectre large, hétérogénéité de régimes |
| α*                | ≈ exposant dominant typique |
| R² moyen scaling  | > 0,98         | scaling log-log très propre |

![MF-DFA BTC — scaling et h(q)](TimeSeries%20And%20Forecasting/btc_mfdfa_real.png)
![Spectre f(α) — BTC](TimeSeries%20And%20Forecasting/btc_falpha_real.png)

> **Lecture** :
> - h(2) > 0,5 → mémoire longue dans la chronique des rendements.
> - h(q) décroissant → la dynamique n'est pas monofractale ; les régimes
>   calmes et de crise n'obéissent pas au même exposant de Hurst.
> - Δα ≈ 0,56 → forte hétérogénéité multi-échelle.

---

## 5. Décomposition des sources de multifractalité

Le test de mélange (Kantelhardt 2002, Éq. 28) permet de séparer les deux
moteurs possibles :

- **Δh_corr** : corrélations longue portée (LRC) — mémoire de la
  volatilité, clustering.
- **Δh_dist** : queues épaisses de la distribution marginale.

![Sources de multifractalité — BTC](TimeSeries%20And%20Forecasting/btc_hq_sources_real.png)

Pour BTC, les deux contributions sont du même ordre de grandeur, avec une
légère prépondérance des **queues épaisses** : la distribution non-gaussienne
porte une part substantielle de la multifractalité, mais la mémoire de la
volatilité reste un ingrédient clé.

Le tableau de bord récapitulatif rassemble les principaux indicateurs :

![Tableau de bord MF-DFA — BTC](TimeSeries%20And%20Forecasting/btc_dashboard_real.png)

---

## 6. Famille GARCH — ce que les modèles capturent (et ce qu'ils manquent)

Trois spécifications avec innovations Student-t sont estimées :

| Modèle           | Mécanisme principal |
|------------------|---------------------|
| **GARCH(1,1)**   | persistance courte de la variance (α + β) |
| **EGARCH(1,1)**  | volatilité asymétrique (effet de levier) |
| **FIGARCH(1,d,1)** | mémoire longue **fractionnaire** dans la variance (paramètre d) |

### 6.1 Volatilité conditionnelle estimée

Les trois modèles produisent des trajectoires de σ̂ₜ comparables, en
particulier autour des chocs (mars 2020, mai 2021, mai 2022).

![Volatilité conditionnelle](TimeSeries%20And%20Forecasting/garch_cond_vol.png)

### 6.2 Multifractalité résiduelle

On relance le MF-DFA sur les **résidus standardisés** ẑₜ pour mesurer la
part de complexité absorbée :

![h(q) — avant/après filtrage GARCH](TimeSeries%20And%20Forecasting/garch_hq_comparison.png)
![Spectres f(α) — avant/après filtrage](TimeSeries%20And%20Forecasting/garch_falpha_comparison.png)

| Modèle              | Δh résiduel | Réduction de Δh | Commentaire |
|---------------------|-------------|-----------------|-------------|
| BTC (rendements)    | ≈ 0,29      | —               | référence |
| GARCH(1,1)-t        | ≈ 0,22      | ≈ 23 %          | absorbe la persistance courte |
| EGARCH(1,1)-t       | ≈ 0,21      | ≈ 28 %          | meilleur AIC, capte l'asymétrie |
| FIGARCH(1,d,1)-t    | ≈ 0,22      | ≈ 25 %          | capte la mémoire longue (d̂ > 0) |

![Résumé comparatif](TimeSeries%20And%20Forecasting/garch_summary.png)

> **Conclusion clé** : aucun modèle GARCH classique n'absorbe entièrement la
> multifractalité (Δh résiduel reste ≥ 0,20). La complexité multi-échelle
> excède donc le cadre d'une **variance conditionnelle scalaire** ; il
> subsiste une dépendance non triviale entre régimes calmes et régimes de
> crise que ces modèles ne représentent pas.

---

## 7. Atelier interactif `garch-mfdfa-dashboard`

L'ensemble du pipeline (statistiques descriptives, GARCH/EGARCH/FIGARCH,
MF-DFA, test de mélange, références théoriques, spectre f(α)) est répliqué
dans une application web minimaliste — **FastAPI** côté backend, **Svelte +
Plotly** côté frontend — avec :

- la série **BTC/USD intégrée** chargeable en un clic,
- l'**import CSV** d'une série quelconque (colonne `returns`, `log_returns`
  ou `rendement`),
- un panneau de paramètres avec **explications inline** pour chaque champ
  MF-DFA (q, échelles, ordre DFA, itérations de mélange…),
- des onglets : Accueil · Descriptif · MF-DFA · Sources · Comparaison.

Démarrage rapide :

```powershell
# Backend
cd garch-mfdfa-dashboard/backend
python -m uvicorn app:app --host 127.0.0.1 --port 8000

# Frontend
cd garch-mfdfa-dashboard/frontend
npm install
npm run dev
```

Voir `garch-mfdfa-dashboard/README.md` et `garch-mfdfa-dashboard/SETUP.md`
pour les détails d'installation.

---

## 8. Structure du dépôt

```
TimeSeries And Forecasting/                 (scripts d'analyse Python)
├── Récupération et préparation des donnée.py
├── Rendements logarithmiques & Analyse descriptive.py
├── mfdfa1.py                               (cœur MF-DFA + références)
├── comparaison_modeles.py                  (GARCH / EGARCH / FIGARCH)
├── btc_prix.csv  /  btc_rendements.csv     (données générées)
└── *.png                                   (figures du présent README)

garch-mfdfa-dashboard/                      (application web)
├── backend/   FastAPI + arch + scipy
└── frontend/  Svelte + Plotly
```

---

## 9. Références

- Kantelhardt, J. W., Zschiegner, S. A., Koscielny-Bunde, E., Havlin, S.,
  Bunde, A., Stanley, H. E. (2002). *Multifractal detrended fluctuation
  analysis of nonstationary time series*. **Physica A**, 316.
- Bollerslev, T. (1986). *Generalized Autoregressive Conditional
  Heteroskedasticity*. **Journal of Econometrics**, 31.
- Nelson, D. B. (1991). *Conditional heteroskedasticity in asset returns: a
  new approach*. **Econometrica**, 59.
- Baillie, R. T., Bollerslev, T., Mikkelsen, H. O. (1996). *Fractionally
  integrated generalized autoregressive conditional heteroskedasticity*.
  **Journal of Econometrics**, 74.
