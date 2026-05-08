import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# ── 2.1  Chargement des données ──────────────────────────────
prix = pd.read_csv("btc_prix.csv",
                   index_col=0, parse_dates=True)
print(f"Données chargées : {len(prix)} observations")

# ── 2.2  Calcul des rendements log ───────────────────────────
# r_t = ln(P_t) - ln(P_{t-1})
prix['log_prix']   = np.log(prix['Prix'])
prix['rendement']  = prix['log_prix'].diff()   # différence première
prix.dropna(inplace=True)                      # supprime la 1re ligne (NaN)

r = prix['rendement']   # alias court pour la suite

print(f"Rendements calculés : {len(r)} observations")
print(f"Période              : {r.index[0].date()} → {r.index[-1].date()}")

# ── 2.3  Statistiques descriptives complètes ─────────────────
print("\n" + "="*50)
print("   STATISTIQUES DESCRIPTIVES — Rendements BTC/USD")
print("="*50)
print(f"  Moyenne          : {r.mean():.6f}")
print(f"  Écart-type (σ)   : {r.std():.6f}")
print(f"  Minimum          : {r.min():.4f}  ({r.idxmin().date()})")
print(f"  Maximum          : {r.max():.4f}  ({r.idxmax().date()})")
print(f"  Skewness         : {r.skew():.4f}  (asymétrie)")
print(f"  Kurtosis (exc.)  : {r.kurtosis():.4f}  (> 0 = queues épaisses)")
print(f"  % jours positifs : {(r > 0).mean()*100:.1f}%")

# ── 2.4  Tests statistiques ──────────────────────────────────
print("\n--- Tests de normalité ---")

# Test Jarque-Bera
jb_stat, jb_pval = stats.jarque_bera(r)
print(f"Jarque-Bera  : stat={jb_stat:,.1f}  p={jb_pval:.2e}",
      "→ NON-normale ✓" if jb_pval < 0.05 else "→ normale")

# Test de Shapiro-Wilk (sur un sous-échantillon de 500 obs max)
sw_stat, sw_pval = stats.shapiro(r.sample(500, random_state=42))
print(f"Shapiro-Wilk : stat={sw_stat:.4f}    p={sw_pval:.2e}",
      "→ NON-normale ✓" if sw_pval < 0.05 else "→ normale")

# Autocorrélation des rendements absolus (proxy volatilité)
from pandas import Series
acf_abs = Series(np.abs(r.values)).autocorr(lag=1)
print(f"\nAutocorrélation |r_t| lag-1 : {acf_abs:.4f}",
      "→ Clustering de volatilité ✓" if acf_abs > 0.1 else "")

# ── 2.5  Sauvegarde ──────────────────────────────────────────
prix[['Prix', 'rendement']].to_csv("btc_rendements.csv")
print("\n[OK] Fichier sauvegardé : btc_rendements.csv")

# ── 2.6  Figure principale (4 graphiques) ────────────────────
fig = plt.figure(figsize=(14, 11))
gs  = gridspec.GridSpec(3, 2, figure=fig, hspace=0.45, wspace=0.35)

ax1 = fig.add_subplot(gs[0, :])   # Ligne 1 : pleine largeur
ax2 = fig.add_subplot(gs[1, 0])
ax3 = fig.add_subplot(gs[1, 1])
ax4 = fig.add_subplot(gs[2, 0])
ax5 = fig.add_subplot(gs[2, 1])

# ── (a) Série des rendements ────────────────────────────────
ax1.plot(r.index, r.values,
         color='#0F6E56', linewidth=0.6, alpha=0.85)
ax1.axhline(0, color='gray', linewidth=0.8, linestyle='--')
ax1.set_title("(a) Rendements logarithmiques journaliers BTC/USD",
              fontsize=11, fontweight='bold')
ax1.set_ylabel("r_t")
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax1.grid(True, alpha=0.25, linestyle='--')

# ── (b) Histogramme + Loi Normale théorique ─────────────────
mu, sigma = r.mean(), r.std()
x_range = np.linspace(r.min(), r.max(), 400)
ax2.hist(r.values, bins=120, density=True,
         color='#378ADD', alpha=0.65, label='Rendements BTC')
ax2.plot(x_range, stats.norm.pdf(x_range, mu, sigma),
         'r-', linewidth=2.2, label='Normale théorique')
ax2.set_title("(b) Distribution des rendements", fontsize=11)
ax2.set_ylabel("Densité"); ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.25, linestyle='--')

# ── (c) Valeur absolue |r_t| — Clusters de volatilité ───────
ax3.plot(r.index, np.abs(r.values),
         color='#BA7517', linewidth=0.6, alpha=0.8)
ax3.set_title("(c) |r_t| — Clusters de volatilité", fontsize=11)
ax3.set_ylabel("|r_t|")
ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax3.grid(True, alpha=0.25, linestyle='--')

# ── (d) QQ-plot ──────────────────────────────────────────────
(osm, osr), (slope, intercept, _) = stats.probplot(r.values,
                                                    dist="norm")
ax4.scatter(osm, osr, s=4, alpha=0.4, color='#185FA5')
ax4.plot(osm, slope*np.array(osm)+intercept,
         'r-', linewidth=1.8)
ax4.set_title("(d) QQ-plot vs loi normale", fontsize=11)
ax4.set_xlabel("Quantiles théoriques")
ax4.set_ylabel("Quantiles observés")
ax4.grid(True, alpha=0.25, linestyle='--')

# ── (e) Autocorrélogramme des r² (ARCH effect) ───────────────
max_lag = 30
acf_vals = [pd.Series(r.values**2).autocorr(lag=k)
            for k in range(1, max_lag+1)]
ci = 1.96 / np.sqrt(len(r))   # intervalle de confiance 95%
ax5.bar(range(1, max_lag+1), acf_vals,
        color='#534AB7', alpha=0.75, width=0.7)
ax5.axhline(ci,  color='red', linestyle='--', linewidth=1,
            label=f'IC 95% (±{ci:.3f})')
ax5.axhline(-ci, color='red', linestyle='--', linewidth=1)
ax5.set_title("(e) ACF de r²_t — Effet ARCH", fontsize=11)
ax5.set_xlabel("Lag"); ax5.set_ylabel("Autocorrélation")
ax5.legend(fontsize=9)
ax5.grid(True, alpha=0.25, linestyle='--')

plt.suptitle("Analyse descriptive des rendements BTC/USD (2017–2024)",
             fontsize=13, fontweight='bold', y=1.01)

plt.savefig("btc_analyse_descriptive.png",
            dpi=150, bbox_inches='tight')
plt.show()
print("[OK] Figure sauvegardée : btc_analyse_descriptive.png")