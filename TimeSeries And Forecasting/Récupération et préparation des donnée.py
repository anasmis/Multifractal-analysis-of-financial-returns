# 

#  ÉTAPE 1 — Récupération et préparation des données BTC/USD
# 


import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import warnings
warnings.filterwarnings('ignore')

# ── 1.1  Paramètres ─────────────────────────────────────────
TICKER = "BTC-USD"       # Bitcoin / Dollar américain
START  = "2017-01-01"    # Début : marché BTC mature
END    = "2024-12-31"    # Fin   : inclut bull/bear cycles

# ── 1.2  Téléchargement via Yahoo Finance ───────────────────
print(f"Téléchargement de {TICKER}  [{START} → {END}]")
raw = yf.download(TICKER, start=START, end=END,
                  auto_adjust=True, progress=False)

print(f"\nDimensions brutes : {raw.shape}")
print(raw.head())

# ── 1.3  Extraction du prix de clôture ajusté ───────────────
# 'Close' = prix de clôture ajusté (splits + dividendes)
prix = raw[['Close']].copy()
prix.columns = ['Prix']

# Suppression des jours sans cotation (NaN)
avant = len(prix)
prix.dropna(inplace=True)
print(f"\nValeurs manquantes supprimées : {avant - len(prix)}")

# Assurer un index datetime propre
prix.index = pd.to_datetime(prix.index)

# ── 1.4  Statistiques de base ────────────────────────────────
print("\n=== Résumé de la série de prix ===")
print(f"Observations : {len(prix)}")
print(f"Période      : {prix.index[0].date()} → {prix.index[-1].date()}")
print(f"Prix min     : {prix['Prix'].min():,.2f} USD")
print(f"Prix max     : {prix['Prix'].max():,.2f} USD")
print(f"Prix moyen   : {prix['Prix'].mean():,.2f} USD")

# ── 1.5  Sauvegarde CSV ──────────────────────────────────────
prix.to_csv("btc_prix.csv")
print("\n[OK] Fichier sauvegardé : btc_prix.csv")

# ── 1.6  Graphique de l'évolution du prix ───────────────────
fig, ax = plt.subplots(figsize=(13, 4))
ax.plot(prix.index, prix['Prix'],
        color='#185FA5', linewidth=0.9, alpha=0.9)
ax.fill_between(prix.index, prix['Prix'],
                alpha=0.08, color='#185FA5')
ax.set_title("BTC/USD — Prix de clôture journalier (2017–2024)",
             fontsize=13, fontweight='bold', pad=10)
ax.set_xlabel("Date")
ax.set_ylabel("Prix (USD)")
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.yaxis.set_major_formatter(
    plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))
ax.grid(True, alpha=0.3, linestyle='--')
plt.tight_layout()
plt.savefig("btc_prix.png", dpi=150, bbox_inches='tight')
plt.show()
print("[OK] Graphique sauvegardé : btc_prix.png")
