"""


Comparaison GARCH vs MF-DFA — BTC/USD 2017-2024
Pipeline :
  1. Estimation GARCH(1,1), EGARCH(1,1), FIGARCH(1,d,1)
  2. Extraction des résidus standardisés ẑ_t = ε_t / √h_t
  3. MF-DFA sur {r_t} et sur {ẑ_t} de chaque modèle
  4. Comparaison h(q), τ(q), Δα — ce que GARCH capture ou non
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import warnings
warnings.filterwarnings('ignore')

from arch import arch_model

# ── Réutilisation des fonctions MF-DFA du pipeline principal ──────────────
from mfdfa1 import (compute_profile, segment_profile, local_variance,
                   fluctuation_function, mfdfa, estimate_hq,
                   compute_falpha)

# 

# 0. DONNÉES BTC
# 


print("=" * 60)
print("  GARCH vs MF-DFA — BTC/USD 2017-2024")
print("=" * 60)
btc_data = pd.read_csv("btc_rendements.csv", index_col=0, parse_dates=True)
returns = btc_data["rendement"].dropna().to_numpy()
r = returns * 100  # arch travaille en % (meilleure convergence numérique)
N = len(r)
# Paramètres MF-DFA communs à toutes les analyses
Q       = np.arange(-5, 6, 1, dtype=float)
SCALES  = np.unique(np.logspace(np.log10(10),
                                np.log10(N // 4), 25).astype(int))
M_ORDER = 1   # DFA1

print(f"\nSérie : N={N} obs | Échelles : [{SCALES[0]}, {SCALES[-1]}] | "
      f"q ∈ [{int(Q[0])}, {int(Q[-1])}]")

# 

# 1. ESTIMATION DES MODÈLES GARCH
# 


def fit_model(returns_pct, vol, p=1, q=1, dist='t'):
    """Estime un modèle ARCH et retourne le résultat + résidus standardisés."""
    if vol == 'FIGARCH':
        # FIGARCH(1,d,1) — moyenne constante, innovations t-Student
        am = arch_model(returns_pct, mean='Constant', vol='FIGARCH',
                        p=p, q=q, dist=dist)
    elif vol == 'EGARCH':
        am = arch_model(returns_pct, mean='Constant', vol='EGARCH',
                        p=p, o=1, q=q, dist=dist)
    else:  # GARCH
        am = arch_model(returns_pct, mean='Constant', vol='GARCH',
                        p=p, q=q, dist=dist)

    res = am.fit(disp='off', options={'maxiter': 500})

    # Résidus standardisés : ẑ_t = ε_t / σ̂_t
    std_resid = res.std_resid
    cond_vol  = res.conditional_volatility   # σ̂_t en %

    return res, std_resid, cond_vol


print("\n[1/3] Estimation GARCH(1,1)-t ...")
res_garch,   z_garch,   vol_garch   = fit_model(r, 'GARCH')

print("[2/3] Estimation EGARCH(1,1)-t ...")
res_egarch,  z_egarch,  vol_egarch  = fit_model(r, 'EGARCH')

print("[3/3] Estimation FIGARCH(1,d,1)-t ...")
res_figarch, z_figarch, vol_figarch = fit_model(r, 'FIGARCH')


# 

# 2. TABLEAU DE COMPARAISON DES MODÈLES
# 


def persistence(res, vol_type):
    """Calcule la persistance de volatilité selon le modèle."""
    p = res.params
    if vol_type == 'GARCH':
        return float(p.get('alpha[1]', 0) + p.get('beta[1]', 0))
    elif vol_type == 'EGARCH':
        return float(p.get('beta[1]', 0))   # AR(1) du log-vol
    else:  # FIGARCH
        return float(p.get('d', np.nan))     # exposant de mémoire longue


print("\n" + "─" * 60)
print(f"  {'Modèle':<12} {'AIC':>9} {'BIC':>9} {'Log-L':>10} {'Persist.':>10}")
print("─" * 60)
for name, res, vt in [("GARCH(1,1)", res_garch,   'GARCH'),
                       ("EGARCH(1,1)",res_egarch,  'EGARCH'),
                       ("FIGARCH",    res_figarch, 'FIGARCH')]:
    pers = persistence(res, vt)
    print(f"  {name:<12} {res.aic:>9.1f} {res.bic:>9.1f} "
          f"{res.loglikelihood:>10.1f} {pers:>10.4f}")
print("─" * 60)

# Paramètres clés
print("\n── Paramètres estimés ──────────────────────────────────")
for name, res in [("GARCH(1,1) ", res_garch),
                   ("EGARCH(1,1)", res_egarch),
                   ("FIGARCH    ", res_figarch)]:
    params_str = "  ".join(f"{k}={v:.4f}"
                           for k, v in res.params.items()
                           if k not in ('nu',))
    print(f"  {name}: {params_str}")

# 

# 3. MF-DFA SUR LES RENDEMENTS ET LES RÉSIDUS
# 


print("\n── MF-DFA en cours ")

def run_mfdfa(x, label):
    """Lance MF-DFA et retourne h(q), τ(q), α, f(α), Δh, Δα."""
    Fq      = mfdfa(x, SCALES, Q, M_ORDER)
    hq, r2  = estimate_hq(SCALES, Fq, Q)
    al, fa, tau = compute_falpha(Q, hq)
    dh      = hq[0] - hq[-1]
    da      = np.max(al) - np.min(al)
    idx_q2  = np.argmin(np.abs(Q - 2))
    print(f"  {label:<24} h(2)={hq[idx_q2]:.3f}  "
          f"Δh={dh:.3f}  Δα={da:.3f}  R²={np.mean(r2):.4f}")
    return hq, tau, al, fa, dh, da

# Rendements originaux (convertis en rendements simples pour MF-DFA)
r_raw = returns   # rendements non scalés pour MF-DFA

hq_r,   tau_r,   al_r,   fa_r,   dh_r,   da_r   = run_mfdfa(r_raw,      "BTC rendements")
hq_g,   tau_g,   al_g,   fa_g,   dh_g,   da_g   = run_mfdfa(z_garch,    "Résidus GARCH(1,1)")
hq_eg,  tau_eg,  al_eg,  fa_eg,  dh_eg,  da_eg  = run_mfdfa(z_egarch,   "Résidus EGARCH(1,1)")
hq_fig, tau_fig, al_fig, fa_fig, dh_fig, da_fig = run_mfdfa(z_figarch,  "Résidus FIGARCH")

# 

# 4. INTERPRÉTATION AUTOMATIQUE
# 


def interpret(dh_orig, dh_resid, da_orig, da_resid, model_name):
    """Imprime l'interprétation de la réduction de multifractalité."""
    red_dh = (dh_orig - dh_resid) / dh_orig * 100
    red_da = (da_orig - da_resid) / da_orig * 100
    print(f"\n  ▶ {model_name}")
    print(f"    Δh : {dh_orig:.3f} → {dh_resid:.3f}  "
          f"(réduction {red_dh:+.1f}%)")
    print(f"    Δα : {da_orig:.3f} → {da_resid:.3f}  "
          f"(réduction {red_da:+.1f}%)")
    if dh_resid > 0.10:
        print(f"    ✗ Multifractalité PERSISTANTE après filtrage — "
              f"complexité non capturée par {model_name}")
    else:
        print(f"    ✓ Multifractalité significativement absorbée")

print("\n" + "═" * 60)
print("  INTERPRÉTATION — Multifractalité résiduelle")
print("═" * 60)
interpret(dh_r, dh_g,   da_r, da_g,   "GARCH(1,1)")
interpret(dh_r, dh_eg,  da_r, da_eg,  "EGARCH(1,1)")
interpret(dh_r, dh_fig, da_r, da_fig, "FIGARCH(1,d,1)")

# Meilleur modèle au sens AIC et au sens de la réduction de multifractalité
best_aic  = min([("GARCH",   res_garch.aic),
                 ("EGARCH",  res_egarch.aic),
                 ("FIGARCH", res_figarch.aic)], key=lambda x: x[1])
best_mf   = min([("GARCH",   dh_g),
                 ("EGARCH",  dh_eg),
                 ("FIGARCH", dh_fig)], key=lambda x: x[1])

print(f"\n  Meilleur AIC   : {best_aic[0]}")
print(f"  Δh résiduel min: {best_mf[0]}  (capture max de mémoire longue)")

idx_q2 = np.argmin(np.abs(Q - 2))
print(f"\n  h(2) BTC original : {hq_r[idx_q2]:.3f}  → "
      f"{'mémoire longue (LRC)' if hq_r[idx_q2]>0.5 else 'pas de LRC'}")
print(f"  FIGARCH d = "
      f"{res_figarch.params.get('d', float('nan')):.3f}  → "
      f"{'longue mémoire fractionnaire' if res_figarch.params.get('d',0)>0 else 'courte mémoire'}")

# 

# 5. FIGURES
# 


COLORS = {'BTC':     '#F5A623',
          'GARCH':   '#7F77DD',
          'EGARCH':  '#1D9E75',
          'FIGARCH': '#D85A30'}

# ── Figure 1 : Volatilité conditionnelle des trois modèles ─────────────────
fig1, axes = plt.subplots(3, 1, figsize=(13, 8), sharex=True)
fig1.suptitle("Volatilité Conditionnelle — GARCH, EGARCH, FIGARCH\n"
              "BTC/USD 2017–2024", fontsize=13, fontweight='bold')

t = np.arange(N)
for ax, vol, name, color in zip(
        axes,
        [vol_garch, vol_egarch, vol_figarch],
        ["GARCH(1,1)", "EGARCH(1,1)", "FIGARCH(1,d,1)"],
        [COLORS['GARCH'], COLORS['EGARCH'], COLORS['FIGARCH']]):
    ax.fill_between(t, 0, vol, alpha=0.35, color=color)
    ax.plot(t, vol, lw=0.7, color=color, label=name)
    ax.set_ylabel("$\\hat{\\sigma}_t$ (%)", fontsize=9)
    ax.legend(fontsize=9, loc='upper right', framealpha=0.8)
    ax.grid(True, ls='--', alpha=0.3)
    # Annotations régimes
    for x, yr in [(0,'2017'),(365,'2018'),(730,'2019'),
                  (1095,'2020'),(1461,'2021'),(1826,'2022')]:
        if x < N:
            ax.axvline(x, color='gray', lw=0.5, alpha=0.4)
            ax.text(x+10, ax.get_ylim()[1]*0.85, yr, fontsize=7, color='gray')

axes[-1].set_xlabel("Jours (2017–2024)", fontsize=10)
plt.tight_layout()
fig1.savefig("garch_cond_vol.png",
             dpi=150, bbox_inches='tight')
print("\n[Fig 1] Volatilité conditionnelle sauvegardée")

# ── Figure 2 : h(q) avant/après filtrage ───────────────────────────────────
fig2, ax = plt.subplots(figsize=(9, 5))
fig2.suptitle("$h(q)$ avant/après filtrage GARCH\n"
              "La multifractalité résiduelle mesure ce que GARCH ne capture pas",
              fontsize=12, fontweight='bold')

ax.plot(Q, hq_r,   'D-',  color=COLORS['BTC'],    lw=2.5, ms=7,
        label=f"BTC rendements    Δh={dh_r:.3f}")
ax.plot(Q, hq_g,   'o--', color=COLORS['GARCH'],  lw=1.8, ms=5,
        label=f"Résidus GARCH     Δh={dh_g:.3f}")
ax.plot(Q, hq_eg,  's--', color=COLORS['EGARCH'], lw=1.8, ms=5,
        label=f"Résidus EGARCH    Δh={dh_eg:.3f}")
ax.plot(Q, hq_fig, '^--', color=COLORS['FIGARCH'],lw=1.8, ms=5,
        label=f"Résidus FIGARCH   Δh={dh_fig:.3f}")
ax.axhline(0.5, color='gray', ls=':', lw=1.0, alpha=0.6, label='h=0.5 (bruit blanc)')

# Zone de persistance
ax.axhspan(0.5, ax.get_ylim()[1] if ax.get_ylim()[1]>0.5 else 0.9,
           alpha=0.04, color='green', label='Zone de persistance')

ax.set_xlabel("Ordre $q$", fontsize=11)
ax.set_ylabel("$h(q)$  [Hurst généralisé]", fontsize=11)
ax.legend(fontsize=9, framealpha=0.85)
ax.grid(True, ls='--', alpha=0.4)

# Annotation Δh résiduel FIGARCH
ax.annotate(f"Δh résiduel\nFIGARCH={dh_fig:.3f}",
            xy=(Q[-1], hq_fig[-1]),
            xytext=(3.0, hq_fig[-1] - 0.08),
            fontsize=8, color=COLORS['FIGARCH'],
            arrowprops=dict(arrowstyle='->', color=COLORS['FIGARCH'], lw=1.0),
            bbox=dict(boxstyle='round', fc='white', ec=COLORS['FIGARCH'], lw=0.8))

plt.tight_layout()
fig2.savefig("garch_hq_comparison.png",
             dpi=150, bbox_inches='tight')
print("[Fig 2] h(q) avant/après filtrage sauvegardé")

# ── Figure 3 : Spectres f(α) superposés ────────────────────────────────────
fig3, ax = plt.subplots(figsize=(8, 5))
fig3.suptitle("Spectres de Singularité $f(\\alpha)$ — Avant/Après Filtrage GARCH\n"
              "Réduction de la largeur Δα = absorption de la multifractalité",
              fontsize=12, fontweight='bold')

for al, fa, name, color, ls, lw in [
        (al_r,   fa_r,   f"BTC (Δα={da_r:.3f})",       COLORS['BTC'],    '-',  2.5),
        (al_g,   fa_g,   f"GARCH (Δα={da_g:.3f})",     COLORS['GARCH'],  '--', 1.8),
        (al_eg,  fa_eg,  f"EGARCH (Δα={da_eg:.3f})",   COLORS['EGARCH'], '--', 1.8),
        (al_fig, fa_fig, f"FIGARCH (Δα={da_fig:.3f})", COLORS['FIGARCH'],'--', 1.8)]:
    ax.plot(al, fa, ls, color=color, lw=lw, marker='o', ms=4, label=name)

ax.axhline(1.0, color='gray', ls='--', lw=0.8, alpha=0.5, label='$f(\\alpha)=1$')
ax.axhline(0.0, color='gray', ls=':', lw=0.7, alpha=0.4)
ax.set_xlabel("$\\alpha$ (exposant de Hölder)", fontsize=11)
ax.set_ylabel("$f(\\alpha)$ (dimension de Hausdorff)", fontsize=11)
ax.legend(fontsize=9, framealpha=0.85)
ax.grid(True, ls='--', alpha=0.4)

# Flèche montrant la contraction du spectre
ax.annotate('', xy=(al_fig[0], fa_fig[0]),
            xytext=(al_r[0], fa_r[0]),
            arrowprops=dict(arrowstyle='->', color='gray',
                            lw=1.2, linestyle='dashed'))
ax.text(min(al_r[0], al_fig[0]) - 0.01,
        (fa_r[0]+fa_fig[0])/2,
        "Contraction\ndu spectre", fontsize=7.5, color='gray',
        ha='right', va='center')

plt.tight_layout()
fig3.savefig("garch_falpha_comparison.png",
             dpi=150, bbox_inches='tight')
print("[Fig 3] Spectres f(α) sauvegardés")

# ── Figure 4 : Tableau de bord résumé ──────────────────────────────────────
fig4, axes4 = plt.subplots(1, 3, figsize=(14, 4.5))
fig4.suptitle("Résumé Comparatif : BTC vs Résidus GARCH — Métriques Multifractales",
              fontsize=12, fontweight='bold')

labels  = ['BTC', 'GARCH\nrésidus', 'EGARCH\nrésidus', 'FIGARCH\nrésidus']
colors4 = [COLORS['BTC'], COLORS['GARCH'], COLORS['EGARCH'], COLORS['FIGARCH']]

# Panel A : Δh
dh_vals = [dh_r, dh_g, dh_eg, dh_fig]
bars = axes4[0].bar(labels, dh_vals, color=colors4, alpha=0.82,
                    edgecolor='white', lw=1.5, width=0.55)
for b, v in zip(bars, dh_vals):
    axes4[0].text(b.get_x()+b.get_width()/2, v+0.004, f'{v:.3f}',
                  ha='center', va='bottom', fontsize=10, fontweight='bold')
axes4[0].set_title("$\\Delta h$ — Amplitude multifractale", fontsize=10, fontweight='bold')
axes4[0].set_ylabel("$\\Delta h = h(q_-) - h(q_+)$", fontsize=9)
axes4[0].set_ylim(0, max(dh_vals)*1.35)
axes4[0].axhline(0.10, color='red', ls='--', lw=0.8, alpha=0.6,
                 label='Seuil sig. (0.10)')
axes4[0].legend(fontsize=7.5)
axes4[0].grid(True, ls='--', alpha=0.3, axis='y')

# Panel B : Δα
da_vals = [da_r, da_g, da_eg, da_fig]
bars2 = axes4[1].bar(labels, da_vals, color=colors4, alpha=0.82,
                     edgecolor='white', lw=1.5, width=0.55)
for b, v in zip(bars2, da_vals):
    axes4[1].text(b.get_x()+b.get_width()/2, v+0.005, f'{v:.3f}',
                  ha='center', va='bottom', fontsize=10, fontweight='bold')
axes4[1].set_title("$\\Delta\\alpha$ — Largeur spectre $f(\\alpha)$",
                   fontsize=10, fontweight='bold')
axes4[1].set_ylabel("$\\Delta\\alpha = \\alpha_{max} - \\alpha_{min}$", fontsize=9)
axes4[1].set_ylim(0, max(da_vals)*1.35)
axes4[1].grid(True, ls='--', alpha=0.3, axis='y')

# Panel C : h(2)
h2_vals = [hq_r[idx_q2], hq_g[idx_q2], hq_eg[idx_q2], hq_fig[idx_q2]]
bars3 = axes4[2].bar(labels, h2_vals, color=colors4, alpha=0.82,
                     edgecolor='white', lw=1.5, width=0.55)
for b, v in zip(bars3, h2_vals):
    axes4[2].text(b.get_x()+b.get_width()/2, v+0.003, f'{v:.3f}',
                  ha='center', va='bottom', fontsize=10, fontweight='bold')
axes4[2].axhline(0.5, color='gray', ls='--', lw=1.0, alpha=0.7,
                 label='h=0.5 (efficient)')
axes4[2].set_title("$h(2)$ — Hurst classique",
                   fontsize=10, fontweight='bold')
axes4[2].set_ylabel("$h(q=2)$", fontsize=9)
axes4[2].set_ylim(0.3, max(h2_vals)*1.2)
axes4[2].legend(fontsize=7.5)
axes4[2].grid(True, ls='--', alpha=0.3, axis='y')

plt.tight_layout()
fig4.savefig("garch_summary.png",
             dpi=150, bbox_inches='tight')
print("[Fig 4] Résumé comparatif sauvegardé")

# 

# 6. CONCLUSION SYNTHÉTIQUE
# 


print("\n" + "═" * 60)
print("  CONCLUSION SYNTHÉTIQUE")
print("═" * 60)

best_filter = min([("GARCH(1,1)",   dh_g),
                   ("EGARCH(1,1)",  dh_eg),
                   ("FIGARCH(1,d,1)", dh_fig)], key=lambda x: x[1])

red_best = (dh_r - best_filter[1]) / dh_r * 100

print(f"\n  Δh original BTC     : {dh_r:.3f}")
print(f"  Δh résiduel minimum : {best_filter[1]:.3f}"
      f"  ({best_filter[0]}, réduction {red_best:.0f}%)")
print(f"\n  → Le meilleur filtre ({best_filter[0]}) absorbe"
      f" {red_best:.0f}% de la multifractalité.")
print(f"  → Il subsiste Δh={best_filter[1]:.3f} de multifractalité résiduelle")
print(f"    irréductible au cadre GARCH — complexité multi-échelle")
print(f"    non capturée par la variance conditionnelle scalaire.")

if res_figarch.params.get('d', 0) > 0.1:
    d_hat = res_figarch.params['d']
    print(f"\n  FIGARCH : d̂ = {d_hat:.3f} > 0 confirme la mémoire longue")
    print(f"  fractionnaire dans la variance (ARCH LM ne suffit pas).")

print(f"\n  Δα BTC={da_r:.3f} vs Δα meilleur résidu={da_fig:.3f}")
print(f"  → {(da_r-da_fig)/da_r*100:.0f}% de la largeur spectrale persiste")
print(f"    après filtrage optimal : la distribution des régimes de")
print(f"    volatilité reste structurellement multifractale.")
print("\nFigures sauvegardées")