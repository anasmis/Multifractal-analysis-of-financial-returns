"""


MF-DFA — Multifractal Detrended Fluctuation Analysis



Série    : BTC/USD log-rendements journaliers
Pipeline : Profil → Segmentation → Detrending → F²(ν,s) → F_q(s) → h(q)


"""

from turtle import pd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


# 

# ÉTAPE 1 — CALCUL DU PROFIL INTÉGRÉ Y(i)
# 


def compute_profile(x):
    """
    Calcule le profil cumulé Y(i) de la série x.

    D'après Kantelhardt (2002), Eq. (1) :
        Y(i) = sum_{k=1}^{i} [x_k - <x>],   i = 1, ..., N

    L'intégration cumulative transforme la série en un processus de type
    marche aléatoire généralisée. Les propriétés de scaling du profil Y(i)
    sont directement reliées aux exposants multifractals de {x_k}.

    Paramètres
    ----------
    x : array (N,)
        Série des log-rendements (ou tout signal stationnaire).

    Retourne
    --------
    Y : array (N,)
        Profil intégré centré sur la moyenne.
    """
    # Soustraire la moyenne avant l'intégration (stabilité numérique)
    x_centered = x - np.mean(x)

    # Somme cumulative = intégration discrète
    Y = np.cumsum(x_centered)

    return Y


# 

# ÉTAPE 2 — SEGMENTATION EN FENÊTRES DE TAILLE s
# 


def segment_profile(Y, s):
    """
    Découpe le profil Y en 2*N_s segments de taille s.

    Kantelhardt (2002) §2.1 : pour traiter le résidu en fin de série,
    on effectue le partitionnement deux fois :
      - Une fois depuis le DÉBUT  → segments ν = 1, ..., N_s
      - Une fois depuis la FIN    → segments ν = N_s+1, ..., 2*N_s

    Cette symétrie garantit que toute la série contribue au calcul,
    même quand N n'est pas un multiple exact de s.

    Paramètres
    ----------
    Y : array (N,)
        Profil intégré.
    s : int
        Taille de la fenêtre (échelle temporelle).

    Retourne
    --------
    segments : list de arrays, chacun de longueur s
        Liste des 2*N_s segments extraits.
    """
    N = len(Y)
    Ns = N // s        # Nombre de segments entiers disponibles

    segments = []

    # Partitionnement depuis le début (segments "forward") 
    for nu in range(Ns):
        start = nu * s
        seg = Y[start : start + s]
        segments.append(seg)

    # --- Partitionnement depuis la fin (segments "backward") ---
    # Garantit que la queue de la série n'est pas ignorée
    for nu in range(Ns):
        start = N - (nu + 1) * s
        seg = Y[start : start + s]
        segments.append(seg)

    return segments   # longueur totale : 2 * Ns


# 

# ÉTAPE 3 & 4 — DETRENDING POLYNOMIAL + VARIANCE LOCALE F²(ν,s)
# 


def local_variance(segment, m):
    """
    Ajuste un polynôme de degré m sur le segment et retourne la variance
    des résidus (variance locale détrencée F²).

    Kantelhardt (2002), Eq. (2) :
        F²(ν, s) = (1/s) * sum_{i=1}^{s} [Y(i) - y_ν(i)]²

    où y_ν(i) est le polynôme ajusté par moindres carrés sur le segment ν.

    Le choix de l'ordre m (DFA-m) détermine quelle tendance polynomiale
    est éliminée : m=1 supprime les tendances linéaires, m=2 les
    quadratiques, etc.

    Paramètres
    ----------
    segment : array (s,)
        Un segment du profil.
    m : int
        Ordre du polynôme de détrending (typiquement 1 ou 2).

    Retourne
    --------
    F2 : float
        Variance locale (>= 0). Renvoie un plancher epsilon si nul
        pour éviter les instabilités numériques pour q < 0.
    """
    s = len(segment)
    i_axis = np.arange(1, s + 1, dtype=float)   # Axe temporel local : 1, 2, ..., s

    # Ajustement polynomial par moindres carrés (numpy.polyfit)
    coeffs = np.polyfit(i_axis, segment, deg=m)
    trend = np.polyval(coeffs, i_axis)

    # Résidus = profil - tendance polynomiale ajustée
    residuals = segment - trend

    # Variance locale : moyenne des résidus au carré
    F2 = np.mean(residuals ** 2)

    # Plancher numérique : évite log(0) et 0^(q/2) pour q < 0
    F2 = max(F2, 1e-10)

    return F2


# 

# ÉTAPE 5 — FONCTION DE FLUCTUATION D'ORDRE q : F_q(s)
# 


def fluctuation_function(F2_list, q):
    """
    Calcule la fonction de fluctuation généralisée F_q(s) pour un ordre q
    donné, à partir de la liste des variances locales F²(ν, s).

    Kantelhardt (2002), Eq. (4) :
        F_q(s) = { (1/2Ns) * sum_ν [F²(ν,s)]^(q/2) }^(1/q),  q ≠ 0

    Cas spécial q = 0, Eq. (6) — moyenne logarithmique :
        F_0(s) = exp{ (1/4Ns) * sum_ν ln[F²(ν,s)] }

    Interprétation de q :
      - q > 0 : les segments à FORTE variance dominent → scaling des crises
      - q < 0 : les segments à FAIBLE variance dominent → scaling des régimes calmes
      - q = 2 : retrouve exactement le DFA standard (exposant de Hurst)

    Paramètres
    ----------
    F2_list : array (2*Ns,)
        Variances locales de chaque segment.
    q : float
        Ordre du moment (q ∈ ℝ, q ≠ 0 pour la formule standard).

    Retourne
    --------
    Fq : float
        Fonction de fluctuation d'ordre q pour l'échelle s courante.
    """
    F2 = np.array(F2_list)
    two_Ns = len(F2)     # = 2 * Ns

    if abs(q) < 1e-8:
        # --- Cas q = 0 : moyenne logarithmique (Eq. 6) ---
        # Équivalent à la limite q → 0 de la formule générale
        Fq = np.exp(0.5 * np.mean(np.log(F2)))

    else:
        # --- Cas général q ≠ 0 (Eq. 4) ---
        # Moyenne des [F²]^(q/2), puis élévation à la puissance 1/q
        mean_val = np.mean(F2 ** (q / 2.0))
        Fq = mean_val ** (1.0 / q)

    return Fq


# 

# ÉTAPE 6 — BOUCLE PRINCIPALE SUR LES ÉCHELLES s ET LES ORDRES q
# 


def mfdfa(x, scales, q_list, m=1):
    """
    Pipeline complet MF-DFA : calcule F_q(s) pour toutes les échelles s
    et tous les ordres q.

    Structure du pipeline (Kantelhardt 2002) :
        x → Y(i) → [segmentation s] → F²(ν,s) → F_q(s) → h(q)

    Paramètres
    ----------
    x      : array (N,)
        Série temporelle des log-rendements.
    scales : array d'entiers
        Grille des échelles s (log-uniforme recommandé).
        Contrainte : s_min >= m+2,  s_max <= N//4.
    q_list : array de floats
        Ordres des moments (ex: np.arange(-5, 6, 1)).
    m      : int (défaut = 1)
        Ordre du polynôme de détrending (DFA1 : m=1, DFA2 : m=2).

    Retourne
    --------
    Fq_matrix : array (len(q_list), len(scales))
        Fq_matrix[i, j] = F_{q_i}(s_j)
    """
    N = len(x)

    # --- Étape 1 : Calcul du profil intégré ---
    Y = compute_profile(x)

    # Initialisation de la matrice de résultats
    Fq_matrix = np.zeros((len(q_list), len(scales)))

    # --- Étape 6 : Boucle sur les échelles s ---
    for j, s in enumerate(scales):

        # Vérification : s doit être assez grand pour ajuster un polynôme de degré m
        if s < m + 2:
            raise ValueError(f"Échelle s={s} trop petite pour DFA-{m}. "
                             f"Requis : s >= {m+2}.")

        # --- Étape 2 : Segmentation en 2*Ns fenêtres ---
        segments = segment_profile(Y, s)

        # --- Étapes 3 & 4 : Calcul de F²(ν,s) pour chaque segment ---
        F2_list = [local_variance(seg, m) for seg in segments]

        # --- Étape 5 : Calcul de F_q(s) pour chaque ordre q ---
        for i, q in enumerate(q_list):
            Fq_matrix[i, j] = fluctuation_function(F2_list, q)

    return Fq_matrix


# 

# ÉTAPE 7 — ESTIMATION DE h(q) PAR RÉGRESSION LOG-LOG
# 


def estimate_hq(scales, Fq_matrix, q_list):
    """
    Estime l'exposant de Hurst généralisé h(q) pour chaque ordre q
    par régression linéaire de ln F_q(s) sur ln s.

    Kantelhardt (2002), Eq. (5) :
        F_q(s) ~ s^{h(q)}
    ⟺  ln F_q(s) = h(q) * ln s + constante

    La pente de cette droite dans le graphe log-log donne h(q).

    Diagnostic :
      - h(q) = 0.5  ∀q  → série aléatoire (bruit blanc)
      - h(q) = H    ∀q  → monofractal (fBm avec Hurst H)
      - h(q) décroissant en q → MULTIFRACTAL
      - h(2) > 0.5          → persistance (volatility clustering)

    Paramètres
    ----------
    scales     : array d'entiers
        Les mêmes échelles s utilisées dans mfdfa().
    Fq_matrix  : array (len(q_list), len(scales))
        Fonctions de fluctuation calculées par mfdfa().
    q_list     : array de floats
        Ordres des moments.

    Retourne
    --------
    hq     : array (len(q_list),)
        Exposants de Hurst généralisés h(q).
    r2     : array (len(q_list),)
        Coefficient R² de chaque régression (qualité du scaling).
    """
    log_s = np.log(scales.astype(float))

    hq = np.zeros(len(q_list))
    r2 = np.zeros(len(q_list))

    for i, q in enumerate(q_list):
        log_Fq = np.log(Fq_matrix[i, :])

        # Régression linéaire : log(Fq) = h(q) * log(s) + cste
        coeffs = np.polyfit(log_s, log_Fq, deg=1)
        hq[i] = coeffs[0]   # Pente = h(q)

        # Calcul du R² pour diagnostiquer la qualité du scaling log-log
        log_Fq_fit = np.polyval(coeffs, log_s)
        ss_res = np.sum((log_Fq - log_Fq_fit) ** 2)
        ss_tot = np.sum((log_Fq - np.mean(log_Fq)) ** 2)
        r2[i] = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0

    return hq, r2


# 

# ÉTAPE 8 — VISUALISATION
# 


def plot_mfdfa(scales, Fq_matrix, q_list, hq, r2, title="MF-DFA"):
    """
    Produit deux graphiques de diagnostic :
      (A) log F_q(s) vs log s  — vérification de la linéarité du scaling
      (B) h(q) vs q            — test de multifractalité

    Paramètres
    ----------
    scales, Fq_matrix, q_list, hq, r2 : sorties de mfdfa() et estimate_hq().
    title : str
        Titre général de la figure.
    """
    log_s = np.log(scales.astype(float))

    # Palette de couleurs continue selon la valeur de q
    cmap = plt.cm.coolwarm
    q_norm = (np.array(q_list) - min(q_list)) / (max(q_list) - min(q_list) + 1e-10)

    fig = plt.figure(figsize=(13, 5))
    fig.suptitle(title, fontsize=13, fontweight='bold', y=1.01)
    gs = gridspec.GridSpec(1, 2, figure=fig, wspace=0.38)

    # ---------------------------------------------------------------
    # PANNEAU A : log F_q(s) vs log s
    # ---------------------------------------------------------------
    ax1 = fig.add_subplot(gs[0])

    for i, q in enumerate(q_list):
        log_Fq = np.log(Fq_matrix[i, :])
        color = cmap(q_norm[i])

        # Données empiriques
        ax1.plot(log_s, log_Fq, 'o', markersize=4, color=color, alpha=0.7)

        # Droite de régression (pente = h(q))
        fit_line = hq[i] * log_s + (np.mean(log_Fq) - hq[i] * np.mean(log_s))
        ax1.plot(log_s, fit_line, '-', linewidth=1.2, color=color,
                 label=f"q={q:.1f} | h={hq[i]:.3f}" if q in [-5, 0, 2, 5] else "")

    ax1.set_xlabel("ln(s)  [échelle temporelle]", fontsize=11)
    ax1.set_ylabel("ln F_q(s)  [log-fluctuation]", fontsize=11)
    ax1.set_title("(A) Scaling log-log de $F_q(s)$\nLinéarité = scaling valide",
                  fontsize=10)
    ax1.legend(fontsize=8, loc="upper left", framealpha=0.8)
    ax1.grid(True, linestyle='--', alpha=0.4)

    # Barre de couleur q
    sm = plt.cm.ScalarMappable(cmap=cmap,
                               norm=plt.Normalize(vmin=min(q_list), vmax=max(q_list)))
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax1, pad=0.02, shrink=0.85)
    cbar.set_label("Ordre q", fontsize=9)

    # ---------------------------------------------------------------
    # PANNEAU B : h(q) vs q
    # ---------------------------------------------------------------
    ax2 = fig.add_subplot(gs[1])

    ax2.plot(q_list, hq, 'o-', color='#3C3489', linewidth=2,
             markersize=6, label="h(q) estimé")

    # Ligne de référence : h = 0.5 (bruit blanc / marché efficient)
    ax2.axhline(0.5, color='gray', linestyle='--', linewidth=1.0,
                label="h = 0.5 (bruit blanc)")

    # Ligne de référence : h = h(2) (Hurst classique)
    idx_q2 = np.argmin(np.abs(np.array(q_list) - 2.0))
    ax2.axhline(hq[idx_q2], color='#D85A30', linestyle=':', linewidth=1.2,
                label=f"h(2) = {hq[idx_q2]:.3f}  (Hurst DFA)")

    # Annoter Δh = amplitude de la multifractalité
    delta_h = hq[0] - hq[-1]
    ax2.annotate(
        f"Δh = {delta_h:.3f}",
        xy=(q_list[len(q_list)//2], (hq[0] + hq[-1]) / 2),
        fontsize=10, color='#3C3489', fontweight='bold',
        ha='center',
        bbox=dict(boxstyle='round,pad=0.3', fc='#EEEDFE', ec='#7F77DD', lw=0.8)
    )

    ax2.set_xlabel("Ordre q", fontsize=11)
    ax2.set_ylabel("h(q)  [Hurst généralisé]", fontsize=11)
    ax2.set_title("(B) $h(q)$ vs $q$\nConstant = monofractal | Décroissant = multifractal",
                  fontsize=10)
    ax2.legend(fontsize=9, framealpha=0.8)
    ax2.grid(True, linestyle='--', alpha=0.4)

    # Qualité des régressions en annotation
    r2_mean = np.mean(r2)
    ax2.text(0.98, 0.05, f"R² moyen = {r2_mean:.4f}",
             transform=ax2.transAxes, fontsize=9,
             ha='right', va='bottom', color='gray')

    plt.tight_layout()
    return fig


# 

# FONCTIONS UTILITAIRES : spectre de singularité f(α) 
# 


def compute_falpha(q_list, hq):
    """
    Calcule le spectre de singularité f(α) via la transformée de Legendre.

    Kantelhardt (2002), Eq. (14) et (16) :
        τ(q)  = q * h(q) - 1
        α     = h(q) + q * h'(q)          [exposant de Hölder]
        f(α)  = q * [α - h(q)] + 1         [dimension de Hausdorff]

    h'(q) est estimé par différences finies centrées.

    Paramètres
    ----------
    q_list : array
    hq     : array — exposants h(q) estimés

    Retourne
    --------
    alpha  : array — exposants de Hölder
    falpha : array — spectre de singularité
    tau    : array — exposant de masse τ(q)
    """
    q = np.array(q_list, dtype=float)
    h = np.array(hq, dtype=float)

    # Exposant de masse τ(q) = q*h(q) - 1
    tau = q * h - 1.0

    # Dérivée h'(q) par différences finies centrées
    dh = np.gradient(h, q)

    # Exposant de Hölder α = h(q) + q * h'(q)
    alpha = h + q * dh

    # Spectre de singularité f(α) = q*(α - h(q)) + 1
    falpha = q * (alpha - h) + 1.0

    return alpha, falpha, tau


def plot_falpha(alpha, falpha, title="Spectre de singularité f(α)"):
    """
    Trace le spectre de singularité f(α).

    Lecture :
      - Δα = α_max - α_min : largeur du spectre (degré de multifractalité)
      - f(α*) = 1          : exposant dominant
      - Asymétrie droite   : queues épaisses dominent
    """
    fig, ax = plt.subplots(figsize=(6.5, 4.5))

    ax.plot(alpha, falpha, 'o-', color='#7F77DD', linewidth=2, markersize=5)

    # Localiser le maximum
    idx_max = np.argmax(falpha)
    ax.plot(alpha[idx_max], falpha[idx_max], '*', color='#D85A30',
            markersize=14, zorder=5, label=f"α* = {alpha[idx_max]:.3f}, f(α*)={falpha[idx_max]:.3f}")

    # Largeur Δα
    delta_alpha = np.max(alpha) - np.min(alpha)
    ax.annotate(
        f"Δα = {delta_alpha:.3f}",
        xy=(np.mean(alpha), falpha[idx_max] * 0.5),
        fontsize=11, color='#534AB7', fontweight='bold', ha='center',
        bbox=dict(boxstyle='round,pad=0.3', fc='#EEEDFE', ec='#7F77DD', lw=0.8)
    )

    ax.axhline(1.0, color='gray', linestyle='--', linewidth=1.0,
               alpha=0.6, label="f(α) = 1  [régime typique]")
    ax.axhline(0.0, color='gray', linestyle=':', linewidth=0.8, alpha=0.5)

    ax.set_xlabel("α  [exposant de Hölder]", fontsize=11)
    ax.set_ylabel("f(α)  [dimension de Hausdorff]", fontsize=11)
    ax.set_title(title, fontsize=11, fontweight='bold')
    ax.legend(fontsize=9, framealpha=0.8)
    ax.grid(True, linestyle='--', alpha=0.4)

    plt.tight_layout()
    return fig


# 

# EXEMPLE D'UTILISATION — SÉRIE SIMULÉE
# 


def generate_test_series(N=2048, series_type='multifractal', seed=42):
    """
    Génère une série de test pour valider l'implémentation.

    Trois types disponibles :
      'white_noise'    → bruit blanc gaussien iid  → h(q) ≈ 0.5 ∀q   (référence)
      'fbm'            → mouvement brownien frac.  → h(q) ≈ H  ∀q   (monofractal)
      'multifractal'   → cascade binomiale         → h(q) décroissant (multifractal)

    Paramètres
    ----------
    N           : int    — longueur de la série
    series_type : str    — type de série ('white_noise', 'fbm', 'multifractal')
    seed        : int    — graine aléatoire pour reproductibilité

    Retourne
    --------
    x : array (N,)  — série simulée
    """
    rng = np.random.default_rng(seed)

    if series_type == 'white_noise':
        # Bruit gaussien iid → h(q) = 0.5 pour tout q
        x = rng.standard_normal(N)

    elif series_type == 'fbm':
        # Approximation fBm par méthode spectrale (H = 0.75 → persistant)
        H = 0.75
        f = np.fft.rfftfreq(N)[1:]             # Fréquences (sans DC)
        power = f ** (-(2 * H + 1) / 2)        # Spectre de puissance fBm
        phases = rng.uniform(0, 2 * np.pi, len(f))
        spectrum = np.zeros(N // 2 + 1, dtype=complex)
        spectrum[1:] = power * np.exp(1j * phases)
        x = np.fft.irfft(spectrum, n=N)
        x = np.diff(x)     # Différenciation → incréments fBm (série stationnaire)
        x = x / np.std(x)  # Normalisation

    elif series_type == 'multifractal':
        # Cascade binomiale multiplicative (Kantelhardt §3.2, paramètre a=0.6)
        # Génère une mesure multifractale sur [0,1] subdivisée récursivement
        a = 0.6           # Paramètre de la cascade : a ∈ (0.5, 1) → multifractal
        n_levels = int(np.log2(N))
        measure = np.ones(1)

        for _ in range(n_levels):
            # À chaque niveau : chaque intervalle est subdivisé en deux,
            # l'un recevant la fraction (a), l'autre (1-a) de la mesure parente
            new_measure = np.empty(len(measure) * 2)
            new_measure[0::2] = measure * a
            new_measure[1::2] = measure * (1 - a)
            measure = new_measure

        measure = measure[:N]

        # Ajouter du bruit pour simuler des rendements réalistes
        x = measure + 0.01 * rng.standard_normal(N)
        x = x / np.std(x)

    else:
        raise ValueError(f"series_type inconnu : '{series_type}'. "
                         "Choisir parmi 'white_noise', 'fbm', 'multifractal'.")

    return x


# 

# FONCTIONS AUXILIAIRES — APPLICATION BTC
# 


def generate_btc_series(seed=2017):
    """
    Génère une série BTC/USD réaliste (2017-2024, N≈2557 jours).

    Approche : Multifractal Random Walk (MRW) — modèle le plus cohérent
    avec la littérature empirique BTC. Le MRW est construit comme :
        r_t = σ_t · z_t
    où σ_t est une volatilité log-normale à mémoire longue (cascade) et
    z_t ~ N(0,1). Ce mécanisme génère directement la multifractalité
    via les corrélations à longue portée de ln σ_t.

    Propriétés cibles (calibration empirique BTC 2017-2024) :
      - h(2) ≈ 0.55–0.65  (persistance LRC)
      - Δh   ≈ 0.20–0.40  (multifractalité significative)
      - Kurtosis excédentaire ≈ 5–12
      - Volatilité ~4% quotidienne
    """
    rng = np.random.default_rng(seed)
    N = 2557

    # --- Étape 1 : Volatilité log-normale à longue mémoire ---
    # Construction d'une série log-normale corrélée (exposant H_vol = 0.8)
    # pour simuler la cascade multiplicative de la volatilité BTC.
    H_vol = 0.82      # Persistance de la volatilité (mémoire longue forte)
    lam2  = 0.18      # Variance du log-vol (λ²=0.18 → Δh significatif)

    # Génération d'un fBm à mémoire longue pour ln(σ)
    # par méthode de Davies-Harte (spectrale)
    n_ext = 2 * N
    freqs = np.fft.rfftfreq(n_ext)[1:]
    power = freqs ** (-(2*H_vol + 1) / 2)
    phases = rng.uniform(0, 2*np.pi, len(freqs))
    spectrum = np.zeros(n_ext//2 + 1, dtype=complex)
    spectrum[1:] = power * np.exp(1j * phases)
    fbm_path = np.fft.irfft(spectrum, n=n_ext)[:N]

    # Volatilité log-normale : σ_t = σ₀ · exp(λ · W_H(t))
    sigma0 = 0.035      # Niveau de base (~3.5% quotidien)
    log_sigma = lam2**0.5 * (fbm_path / fbm_path.std())
    sigma_t = sigma0 * np.exp(log_sigma)

    # --- Étape 2 : Rendements = σ_t · z_t  (innovations gaussiennes) ---
    # Innovations t-Student ν=4 : queues épaisses réalistes BTC
    z_t = rng.standard_t(df=4, size=N)
    returns = sigma_t * z_t

    # Normalisation finale à ~4% de volatilité quotidienne
    returns = returns / returns.std() * 0.040

    # --- Étape 3 : Régimes historiques (modulation douce ±30%) ---
    # Facteurs proches de 1 pour préserver les propriétés multifractales
    regime_vol = np.ones(N)
    regime_vol[0:200]    = 1.25   # 2017 : bull précoce
    regime_vol[200:420]  = 1.40   # Bull 2017 : ATH
    regime_vol[420:750]  = 1.20   # Bear 2018
    regime_vol[750:1000] = 0.90   # 2019 : consolidation
    regime_vol[1000:1080]= 1.60   # COVID crash 2020
    regime_vol[1080:1460]= 1.25   # Bull 2020-2021
    regime_vol[1460:1830]= 1.15   # Bear 2022
    regime_vol[1830:]    = 1.00   # Recovery 2023-2024

    # Lissage gaussien des transitions (σ=15 jours)
    from scipy.ndimage import gaussian_filter1d
    regime_smooth = gaussian_filter1d(regime_vol.astype(float), sigma=15)
    returns = returns * regime_smooth

    prices = np.zeros(N + 1)
    prices[0] = 1000.0
    for t in range(N):
        prices[t+1] = prices[t] * np.exp(returns[t])

    years = (['2017']*365 + ['2018']*365 + ['2019']*365 +
             ['2020']*366 + ['2021']*365 + ['2022']*365 +
             ['2023']*365 + ['2024']*(N - 365*6 - 366))
    dates = years[:N]

    return returns, prices, dates


def compute_descriptive_stats(x):
    """Statistiques descriptives essentielles pour la série x."""
    from scipy import stats as sp_stats
    mu, sigma = np.mean(x), np.std(x)
    skew  = float(sp_stats.skew(x))
    kurt  = float(sp_stats.kurtosis(x))
    jb    = float(sp_stats.jarque_bera(x).statistic)
    jb_p  = float(sp_stats.jarque_bera(x).pvalue)
    abs_x = np.abs(x - mu)
    acf1  = float(np.corrcoef(abs_x[:-1],  abs_x[1:])[0,1])
    acf5  = float(np.corrcoef(abs_x[:-5],  abs_x[5:])[0,1])
    acf20 = float(np.corrcoef(abs_x[:-20], abs_x[20:])[0,1])
    return {
        "Moyenne journalière":        f"{mu:.5f}",
        "Écart-type (vol. journ.)":   f"{sigma:.4f}  (~{sigma*np.sqrt(252)*100:.0f}% annualisé)",
        "Asymétrie γ₁":               f"{skew:.3f}",
        "Kurtosis excédentaire":      f"{kurt:.2f}  (Gaussienne = 0)",
        "Jarque-Bera (stat / p-val)": f"{jb:.1f}  /  {jb_p:.2e}",
        "ACF(|r|) lag-1 / 5 / 20":   f"{acf1:.3f}  /  {acf5:.3f}  /  {acf20:.3f}",
    }


def shuffling_test(x, scales, q_list, m, M=30):
    """
    Test de mélange (Kantelhardt 2002, Eq. 28).
    Décompose Δh_total = Δh_corr (corrélations LRC) + Δh_dist (queues).
    """
    rng = np.random.default_rng(42)
    hq_shuf_all = np.zeros((M, len(q_list)))
    for m_idx in range(M):
        x_perm = rng.permutation(x)
        Fq_p   = mfdfa(x_perm, scales, q_list, m)
        hq_p, _= estimate_hq(scales, Fq_p, q_list)
        hq_shuf_all[m_idx] = hq_p
    hq_shuf = hq_shuf_all.mean(axis=0)

    Fq_orig    = mfdfa(x, scales, q_list, m)
    hq_orig, _ = estimate_hq(scales, Fq_orig, q_list)
    delta_h_total = hq_orig[0]  - hq_orig[-1]
    delta_h_dist  = hq_shuf[0]  - hq_shuf[-1]
    delta_h_corr  = delta_h_total - delta_h_dist
    return hq_shuf, delta_h_corr, delta_h_dist


def plot_btc_overview(prices, returns, dates, stats):
    """Vue d'ensemble BTC : prix, rendements, distribution, ACF(|r|)."""
    N   = len(returns)
    fig = plt.figure(figsize=(14, 9))
    fig.suptitle("BTC/USD — Analyse Exploratoire (2017–2024)",
                 fontsize=14, fontweight='bold', y=0.98)
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.38, wspace=0.32)

    year_ticks  = [0, 365, 730, 1096, 1462, 1827, 2192, 2557]
    year_labels = ['Jan\n2017','Jan\n2018','Jan\n2019','Jan\n2020',
                   'Jan\n2021','Jan\n2022','Jan\n2023','Jan\n2024']
    regime_colors = {'2017':'#F5A623','2018':'#D0021B','2019':'#7B7B7B',
                     '2020':'#9B59B6','2021':'#27AE60','2022':'#E74C3C',
                     '2023':'#2980B9','2024':'#1ABC9C'}

    # --- Prix (log) ---
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.semilogy(prices, color='#2C3E50', linewidth=0.9, alpha=0.85)
    regime_bounds = [(0,200,'2017'),(200,420,'2017'),(420,750,'2018'),
                     (750,1000,'2019'),(1000,1080,'2020'),(1080,1460,'2021'),
                     (1460,1830,'2022'),(1830,N,'2023')]
    for s, e, yr in regime_bounds:
        ax1.axvspan(s, e, alpha=0.07, color=regime_colors.get(yr,'gray'))
    ax1.set_xticks([t for t in year_ticks if t < len(prices)])
    ax1.set_xticklabels(year_labels[:sum(t < len(prices) for t in year_ticks)], fontsize=7.5)
    ax1.set_ylabel("Prix BTC (USD, log-scale)", fontsize=10)
    ax1.set_title("Série des prix", fontsize=10, fontweight='bold')
    ax1.grid(True, linestyle='--', alpha=0.3, which='both')

    # --- Rendements ---
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.plot(returns, color='#2980B9', linewidth=0.5, alpha=0.75)
    ax2.axhline(0, color='black', linewidth=0.6, alpha=0.4)
    sigma = returns.std()
    ax2.axhspan(-2*sigma,  2*sigma, alpha=0.07, color='green',  label='±2σ')
    ax2.axhspan(-3*sigma,  3*sigma, alpha=0.04, color='orange', label='±3σ')
    ax2.axhspan(returns.min(), -3*sigma, alpha=0.08, color='red')
    ax2.axhspan(3*sigma, returns.max(), alpha=0.08, color='red', label='|r|>3σ')
    ax2.set_xticks([t for t in year_ticks if t < N])
    ax2.set_xticklabels(year_labels[:sum(t < N for t in year_ticks)], fontsize=7.5)
    ax2.set_ylabel("Log-rendements $r_t$", fontsize=10)
    ax2.set_title("Log-rendements journaliers", fontsize=10, fontweight='bold')
    ax2.legend(fontsize=7.5, loc='upper right', framealpha=0.8)
    ax2.grid(True, linestyle='--', alpha=0.3)

    # --- Distribution vs Gaussienne ---
    ax3 = fig.add_subplot(gs[1, 0])
    bins = np.linspace(np.percentile(returns,0.1), np.percentile(returns,99.9), 100)
    ax3.hist(returns, bins=bins, density=True, color='#3C3489', alpha=0.65, label='Empirique')
    mu_r, sig_r = returns.mean(), returns.std()
    xg = np.linspace(bins[0], bins[-1], 400)
    gauss = np.exp(-0.5*((xg-mu_r)/sig_r)**2)/(sig_r*np.sqrt(2*np.pi))
    ax3.plot(xg, gauss, 'r-', linewidth=2, label='$\\mathcal{N}(\\mu,\\sigma^2)$')
    kurt_val = float(stats["Kurtosis excédentaire"].split()[0])
    ax3.text(0.97, 0.95, f"Kurt exc. = {kurt_val:.1f}\n(Gaussienne = 0)",
             transform=ax3.transAxes, fontsize=8.5, ha='right', va='top',
             bbox=dict(boxstyle='round', fc='#EEEDFE', ec='#7F77DD', lw=0.8))
    ax3.set_xlabel("$r_t$", fontsize=10)
    ax3.set_ylabel("Densité", fontsize=10)
    ax3.set_title("Distribution vs Gaussienne", fontsize=10, fontweight='bold')
    ax3.legend(fontsize=9, framealpha=0.8)
    ax3.grid(True, linestyle='--', alpha=0.3)

    # --- ACF(|r|) ---
    ax4 = fig.add_subplot(gs[1, 1])
    max_lag = 150
    abs_r   = np.abs(returns - returns.mean())
    acf_vals = np.array([np.corrcoef(abs_r[:-k], abs_r[k:])[0,1]
                         if k > 0 else 1.0 for k in range(max_lag+1)])
    lags = np.arange(max_lag+1)
    ax4.bar(lags[1:], acf_vals[1:], color='#1D9E75', alpha=0.7, width=1.0, label='ACF($|r_t|$)')
    ci = 1.96 / np.sqrt(N)
    ax4.axhline(ci,  color='red', linestyle='--', linewidth=1.2, label=f'±95% IC')
    ax4.axhline(-ci, color='red', linestyle='--', linewidth=1.2)
    ax4.axhline(0,   color='black', linewidth=0.6, alpha=0.4)
    # Ajustement loi puissance
    lags_fit, acf_fit = lags[1:61], acf_vals[1:61]
    valid = acf_fit > 0
    if valid.sum() > 5:
        coef = np.polyfit(np.log(lags_fit[valid]), np.log(acf_fit[valid]), 1)
        gamma_hat = -coef[0]
        ax4.plot(lags_fit, np.exp(coef[1]) * lags_fit**coef[0], 'k-',
                 linewidth=1.8, alpha=0.7, label=f'Loi puissance $\\gamma$≈{gamma_hat:.2f}')
    ax4.set_xlabel("Lag $k$ (jours)", fontsize=10)
    ax4.set_ylabel("Autocorrélation", fontsize=10)
    ax4.set_title("ACF de $|r_t|$ — Mémoire longue", fontsize=10, fontweight='bold')
    ax4.legend(fontsize=8, framealpha=0.8)
    ax4.set_xlim([0, max_lag])
    ax4.grid(True, linestyle='--', alpha=0.3)
    return fig


def plot_btc_vs_references(q_list, hq_btc, hq_shuf, hq_wn, hq_mf,
                            delta_h_total, delta_h_corr, delta_h_dist):
    """Décomposition des sources de multifractalité BTC — 2 panneaux."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle("Sources de Multifractalité — BTC/USD",
                 fontsize=13, fontweight='bold')

    # Gauche : BTC vs références
    ax = axes[0]
    ax.plot(q_list, hq_wn,  'o--', color='#888780', linewidth=1.6, markersize=5,
            label="Bruit blanc ($h≈0.5$)")
    ax.plot(q_list, hq_mf,  's--', color='#1D9E75', linewidth=1.6, markersize=5,
            label=f"Cascade binomiale ($\\Delta h={hq_mf[0]-hq_mf[-1]:.2f}$)")
    ax.plot(q_list, hq_btc, 'D-',  color='#F5A623', linewidth=2.5, markersize=7,
            label=f"BTC/USD 2017–2024 ($\\Delta h={delta_h_total:.3f}$)")
    ax.axhline(0.5, color='gray', linestyle=':', linewidth=1.0, alpha=0.5)
    idx_q2 = np.argmin(np.abs(np.array(q_list) - 2.0))
    ax.annotate(f"h(2)={hq_btc[idx_q2]:.3f}",
                xy=(2, hq_btc[idx_q2]), xytext=(3.0, hq_btc[idx_q2]+0.06),
                fontsize=8.5, color='#F5A623',
                arrowprops=dict(arrowstyle='->', color='#F5A623', lw=1.2),
                bbox=dict(boxstyle='round', fc='#FFF3DC', ec='#F5A623', lw=0.8))
    ax.set_xlabel("Ordre $q$", fontsize=11)
    ax.set_ylabel("$h(q)$", fontsize=11)
    ax.set_title("BTC vs Références", fontsize=10, fontweight='bold')
    ax.legend(fontsize=8.5, framealpha=0.85)
    ax.grid(True, linestyle='--', alpha=0.4)

    # Droit : décomposition sources
    ax2 = axes[1]
    ax2.plot(q_list, hq_btc,  'D-',  color='#F5A623', linewidth=2.5, markersize=7,
             label=f"BTC original — $\\Delta h_{{total}}={delta_h_total:.3f}$")
    ax2.plot(q_list, hq_shuf, 'o--', color='#D85A30', linewidth=1.8, markersize=6,
             label=f"Série mélangée — $\\Delta h_{{dist}}={delta_h_dist:.3f}$")
    ax2.axhline(0.5, color='gray', linestyle=':', linewidth=1.0, alpha=0.5)
    ax2.fill_between(q_list, hq_shuf, hq_btc, alpha=0.18, color='#7F77DD',
                     label=f"$\\Delta h_{{corr}}={delta_h_corr:.3f}$ (LRC)")
    pct = delta_h_corr / delta_h_total * 100 if delta_h_total > 0 else 0
    ax2.text(0.04, 0.50,
             f"Sources :\n  LRC   : {pct:.0f}%\n  Queues: {100-pct:.0f}%",
             transform=ax2.transAxes, fontsize=9,
             bbox=dict(boxstyle='round', fc='#EEEDFE', ec='#7F77DD', lw=0.8))
    ax2.set_xlabel("Ordre $q$", fontsize=11)
    ax2.set_ylabel("$h(q)$", fontsize=11)
    ax2.set_title("Décomposition : Corrélations vs Queues\n"
                  "(Test de mélange — Kantelhardt 2002)",
                  fontsize=10, fontweight='bold')
    ax2.legend(fontsize=8, framealpha=0.85)
    ax2.grid(True, linestyle='--', alpha=0.4)
    plt.tight_layout()
    return fig


def plot_dashboard(q_list, hq_btc, hq_wn, alpha_btc, falpha_btc,
                   tau_btc, returns, stats,
                   delta_h, delta_h_corr, delta_h_dist):
    """Tableau de bord complet MF-DFA BTC — 6 panneaux synthétiques."""
    fig = plt.figure(figsize=(15, 10))
    fig.suptitle("Tableau de Bord MF-DFA — BTC/USD 2017–2024",
                 fontsize=15, fontweight='bold', y=0.99)
    gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.42, wspace=0.35)

    idx_q2  = np.argmin(np.abs(np.array(q_list) - 2.0))
    sigma   = returns.std()
    cmap_q  = plt.cm.coolwarm
    q_arr   = np.array(q_list)
    q_norm  = (q_arr - q_arr.min()) / (q_arr.max() - q_arr.min() + 1e-10)

    # [0,0] h(q) vs q
    ax00 = fig.add_subplot(gs[0, 0])
    for i in range(len(q_list)):
        ax00.plot(q_list[i], hq_btc[i], 'o', color=cmap_q(q_norm[i]), markersize=8, zorder=3)
    ax00.plot(q_list, hq_btc, '-',  color='#F5A623', linewidth=2.0, zorder=2,
              label=f"BTC ($\\Delta h={delta_h:.3f}$)")
    ax00.plot(q_list, hq_wn,  '--', color='#888780', linewidth=1.3, alpha=0.7,
              label="Bruit blanc ($h=0.5$)")
    ax00.axhline(0.5, color='gray', linestyle=':', alpha=0.5)
    ax00.set_xlabel("Ordre $q$", fontsize=10)
    ax00.set_ylabel("$h(q)$", fontsize=10)
    ax00.set_title("Hurst Généralisé $h(q)$", fontsize=10, fontweight='bold')
    ax00.legend(fontsize=8, framealpha=0.8)
    ax00.grid(True, linestyle='--', alpha=0.35)
    sm = plt.cm.ScalarMappable(cmap=cmap_q,
         norm=plt.Normalize(vmin=min(q_list), vmax=max(q_list)))
    sm.set_array([])
    fig.colorbar(sm, ax=ax00, shrink=0.8, pad=0.02, label='q')

    # [0,1] τ(q) non-linéarité
    ax01 = fig.add_subplot(gs[0, 1])
    tau_mono = q_arr * hq_btc[idx_q2] - 1
    ax01.plot(q_list, tau_btc,  'D-', color='#3C3489', linewidth=2.2, markersize=6,
              label="$\\tau(q)$ BTC")
    ax01.plot(q_list, tau_mono, '--', color='#888780', linewidth=1.5, alpha=0.8,
              label=f"Monofractal $H={hq_btc[idx_q2]:.2f}$")
    ax01.fill_between(q_list, tau_mono, tau_btc, alpha=0.15, color='#7F77DD',
                      label="Écart multifractal")
    ax01.set_xlabel("Ordre $q$", fontsize=10)
    ax01.set_ylabel("$\\tau(q)=qh(q)-1$", fontsize=10)
    ax01.set_title("Exposant de Masse $\\tau(q)$\nNon-linéarité = Multifractalité",
                   fontsize=10, fontweight='bold')
    ax01.legend(fontsize=8, framealpha=0.8)
    ax01.grid(True, linestyle='--', alpha=0.35)

    # [0,2] Spectre f(α)
    ax02 = fig.add_subplot(gs[0, 2])
    ax02.plot(alpha_btc, falpha_btc, 'o-', color='#7F77DD', linewidth=2.2, markersize=5)
    idx_max = np.argmax(falpha_btc)
    ax02.plot(alpha_btc[idx_max], falpha_btc[idx_max], '*',
              color='#D85A30', markersize=16, zorder=5,
              label=f"$\\alpha^*={alpha_btc[idx_max]:.3f}$")
    delta_alpha = np.max(alpha_btc) - np.min(alpha_btc)
    ax02.annotate(f"$\\Delta\\alpha={delta_alpha:.3f}$",
                  xy=(np.mean(alpha_btc), max(falpha_btc)*0.45),
                  fontsize=10, ha='center', color='#3C3489', fontweight='bold',
                  bbox=dict(boxstyle='round', fc='#EEEDFE', ec='#7F77DD', lw=0.8))
    ax02.axhline(1.0, color='gray', linestyle='--', linewidth=1.0, alpha=0.6,
                 label='$f(\\alpha)=1$')
    ax02.axhline(0.0, color='gray', linestyle=':', linewidth=0.8, alpha=0.4)
    ax02.set_xlabel("$\\alpha$ (Hölder)", fontsize=10)
    ax02.set_ylabel("$f(\\alpha)$ (dim. Hausdorff)", fontsize=10)
    ax02.set_title("Spectre de Singularité $f(\\alpha)$",
                   fontsize=10, fontweight='bold')
    ax02.legend(fontsize=8.5, framealpha=0.8)
    ax02.grid(True, linestyle='--', alpha=0.35)

    # [1,0] Queues épaisses — CCDF log-log
    ax10 = fig.add_subplot(gs[1, 0])
    abs_r   = np.abs(returns)
    abs_sorted = np.sort(abs_r)[::-1]
    n = len(abs_sorted)
    ccdf = np.arange(1, n+1) / n
    ax10.loglog(abs_sorted, ccdf, '.', color='#2980B9',
                markersize=2, alpha=0.5, label='CCDF empirique BTC')
    thresh = np.percentile(abs_r, 85)
    mask = abs_sorted > thresh
    if mask.sum() > 20:
        lx = np.log(abs_sorted[mask])
        ly = np.log(ccdf[mask])
        coef = np.polyfit(lx, ly, 1)
        nu_hat = -coef[0]
        ax10.loglog(abs_sorted[mask], np.exp(coef[1]) * abs_sorted[mask]**coef[0],
                    'r-', linewidth=2.0, label=f"Loi puissance $\\nu\\approx{nu_hat:.1f}$")
    ax10.set_xlabel("$|r_t|$  (log-scale)", fontsize=10)
    ax10.set_ylabel("$P(|r|>x)$  (log-scale)", fontsize=10)
    ax10.set_title("Queues Épaisses — CCDF log-log", fontsize=10, fontweight='bold')
    ax10.legend(fontsize=8, framealpha=0.8)
    ax10.grid(True, linestyle='--', alpha=0.35, which='both')

    # [1,1] Décomposition sources (barres)
    ax11 = fig.add_subplot(gs[1, 1])
    categories = ['$\\Delta h_{total}$',
                  '$\\Delta h_{corr}$\n(corrélations)',
                  '$\\Delta h_{dist}$\n(queues)']
    values = [delta_h, delta_h_corr, delta_h_dist]
    colors = ['#F5A623', '#7F77DD', '#D85A30']
    bars = ax11.bar(categories, values, color=colors,
                    alpha=0.82, edgecolor='white', linewidth=1.5, width=0.55)
    for bar, val in zip(bars, values):
        ax11.text(bar.get_x() + bar.get_width()/2,
                  bar.get_height() + 0.004,
                  f'{val:.3f}', ha='center', va='bottom',
                  fontsize=10, fontweight='bold')
    pct_corr = delta_h_corr / delta_h * 100 if delta_h > 0 else 0
    ax11.text(0.97, 0.96,
              f"LRC : {pct_corr:.0f}%\nQueues : {100-pct_corr:.0f}%",
              transform=ax11.transAxes, fontsize=9.5, ha='right', va='top',
              bbox=dict(boxstyle='round', fc='#EEEDFE', ec='#7F77DD', lw=0.8))
    ax11.set_ylabel("Amplitude $\\Delta h$", fontsize=10)
    ax11.set_title("Sources de Multifractalité\n(Test de mélange)",
                   fontsize=10, fontweight='bold')
    ax11.set_ylim(0, max(values)*1.35)
    ax11.grid(True, linestyle='--', alpha=0.35, axis='y')

    # [1,2] Tableau récapitulatif
    ax12 = fig.add_subplot(gs[1, 2])
    ax12.axis('off')
    kurt_val = float(stats["Kurtosis excédentaire"].split()[0])
    skew_val = float(stats["Asymétrie γ₁"])
    table_data = [
        ["Métrique",         "Valeur",                    "Interprétation"],
        ["$h(2)$",           f"{hq_btc[idx_q2]:.3f}",    "Persistance LRC"],
        ["$\\Delta h$",      f"{delta_h:.3f}",            "Multifractalité"],
        ["$\\Delta\\alpha$", f"{delta_alpha:.3f}",        "Hétérogénéité"],
        ["$\\alpha^*$",      f"{alpha_btc[idx_max]:.3f}", "Régime typique"],
        ["Kurt. exc.",       f"{kurt_val:.1f}",           "Queues épaisses"],
        ["Asymétrie",        f"{skew_val:.3f}",           "Crash > rally"],
        ["LRC part",         f"{pct_corr:.0f}%",          "Source dominante"],
    ]
    col_widths = [0.38, 0.28, 0.34]
    row_h = 0.112
    for r, row in enumerate(table_data):
        y_pos = 0.93 - r * row_h
        fc = '#3C3489' if r == 0 else ('#F0EFF8' if r % 2 == 0 else 'white')
        tc = 'white' if r == 0 else 'black'
        x = 0.0
        for c, (cell, cw) in enumerate(zip(row, col_widths)):
            rect = plt.Rectangle((x, y_pos - row_h*0.85), cw - 0.01, row_h*0.88,
                                  transform=ax12.transAxes,
                                  fc=fc, ec='#CCCCCC', lw=0.5, clip_on=False)
            ax12.add_patch(rect)
            ax12.text(x + cw/2, y_pos - row_h*0.4, cell,
                      transform=ax12.transAxes,
                      ha='center', va='center', fontsize=8.5,
                      fontweight='bold' if r == 0 else 'normal', color=tc)
            x += cw
    ax12.set_title("Récapitulatif des Métriques Clés",
                   fontsize=10, fontweight='bold', pad=10)
    return fig


# 

# SCRIPT PRINCIPAL
# 


if __name__ == "__main__":

    print("=" * 65)
    print("  MF-DFA ")
    print("  Démonstration sur séries simulées")
    print("=" * 65)

    # ------------------------------------------------------------------
    # PARAMÈTRES GLOBAUX
    # ------------------------------------------------------------------
    N        = 2048           # Longueur de la série
    m        = 1              # Ordre de détrending : DFA1 (linéaire)
    q_list   = np.arange(-5, 6, 1, dtype=float)    # q ∈ {-5, ..., +5}

    # Grille d'échelles log-uniforme : de s_min=10 à N//4, 25 points
    s_min    = max(10, m + 2)
    s_max    = N // 4
    scales   = np.unique(
        np.logspace(np.log10(s_min), np.log10(s_max), num=25).astype(int)
    )

    print(f"\nParamètres :")
    print(f"  Longueur série  N  = {N}")
    print(f"  Ordre DFA       m  = {m}")
    print(f"  Plage échelles     = [{scales[0]}, {scales[-1]}]  ({len(scales)} points)")
    print(f"  Ordres q           = {q_list.tolist()}")

    # ------------------------------------------------------------------
    # TEST 1 : BRUIT BLANC — validation (h(q) ≈ 0.5 ∀q attendu)
    # ------------------------------------------------------------------
    print("\n[1/3] Bruit blanc gaussien (référence h=0.5)...")
    x_wn = generate_test_series(N, 'white_noise')
    Fq_wn = mfdfa(x_wn, scales, q_list, m)
    hq_wn, r2_wn = estimate_hq(scales, Fq_wn, q_list)
    print(f"      h(q=2) = {hq_wn[list(q_list).index(2)]:.3f}  [attendu ≈ 0.50]")
    print(f"      Δh     = {hq_wn[0]-hq_wn[-1]:.3f}  [attendu ≈ 0.00]")

    # ------------------------------------------------------------------
    # TEST 2 : fBm — monofractal (h(q) ≈ H ∀q attendu, H=0.75)
    # ------------------------------------------------------------------
    print("\n[2/3] Mouvement brownien fractionnaire H=0.75 (monofractal)...")
    x_fbm = generate_test_series(N, 'fbm')
    Fq_fbm = mfdfa(x_fbm, scales, q_list, m)
    hq_fbm, r2_fbm = estimate_hq(scales, Fq_fbm, q_list)
    print(f"      h(q=2) = {hq_fbm[list(q_list).index(2)]:.3f}  [attendu ≈ 0.75]")
    print(f"      Δh     = {hq_fbm[0]-hq_fbm[-1]:.3f}  [attendu faible]")

    # ------------------------------------------------------------------
    # TEST 3 : Cascade binomiale — multifractal
    # ------------------------------------------------------------------
    print("\n[3/3] Cascade binomiale a=0.6 (multifractal attendu)...")
    x_mf = generate_test_series(N, 'multifractal')
    Fq_mf = mfdfa(x_mf, scales, q_list, m)
    hq_mf, r2_mf = estimate_hq(scales, Fq_mf, q_list)
    print(f"      h(q=2) = {hq_mf[list(q_list).index(2)]:.3f}")
    print(f"      Δh     = {hq_mf[0]-hq_mf[-1]:.3f}  [attendu > 0 significatif]")
    print(f"      R² moy = {np.mean(r2_mf):.4f}  [qualité du scaling log-log]")

    # ------------------------------------------------------------------
    # SPECTRE f(α) pour la cascade multifractale
    # ------------------------------------------------------------------
    alpha_mf, falpha_mf, tau_mf = compute_falpha(q_list, hq_mf)

    # ------------------------------------------------------------------
    # RÉSUMÉ COMPARATIF
    # ------------------------------------------------------------------
    print("\n" + "-" * 65)
    print(f"  {'Série':<25} {'h(2)':<10} {'Δh':<10} {'R² moy'}")
    print("-" * 65)
    print(f"  {'Bruit blanc':<25} {hq_wn[5]:<10.3f} {hq_wn[0]-hq_wn[-1]:<10.3f} {np.mean(r2_wn):.4f}")
    print(f"  {'fBm (H=0.75)':<25} {hq_fbm[5]:<10.3f} {hq_fbm[0]-hq_fbm[-1]:<10.3f} {np.mean(r2_fbm):.4f}")
    print(f"  {'Cascade binomiale':<25} {hq_mf[5]:<10.3f} {hq_mf[0]-hq_mf[-1]:<10.3f} {np.mean(r2_mf):.4f}")
    print("-" * 65)
    print("\nInterprétation :")
    print("  Δh ≈ 0  → monofractal (bruit blanc ou fBm)")
    print("  Δh > 0  → multifractal (cascade, marché crypto)")

    # ------------------------------------------------------------------
    # VISUALISATIONS
    # ------------------------------------------------------------------
    print("\nGénération des figures...")

    fig1 = plot_mfdfa(scales, Fq_wn, q_list, hq_wn, r2_wn,
                      title="MF-DFA — Bruit blanc gaussien (référence)")

    fig2 = plot_mfdfa(scales, Fq_mf, q_list, hq_mf, r2_mf,
                      title="MF-DFA — Cascade binomiale a=0.6 (multifractal)")

    fig3 = plot_falpha(alpha_mf, falpha_mf,
                       title="Spectre de singularité f(α) — Cascade binomiale")

    # Comparaison h(q) des trois séries sur un seul graphe
    fig4, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(q_list, hq_wn,  'o--', color="#FC0B0B", linewidth=1.8,
            markersize=5, label="Bruit blanc  [Δh≈0]")
    ax.plot(q_list, hq_fbm, 's--', color='#1D9E75', linewidth=1.8,
            markersize=5, label=f"fBm H=0.75  [Δh≈{hq_fbm[0]-hq_fbm[-1]:.2f}]")
    ax.plot(q_list, hq_mf,  'D-',  color='#7F77DD', linewidth=2.2,
            markersize=6, label=f"Cascade     [Δh≈{hq_mf[0]-hq_mf[-1]:.2f}]")
    ax.axhline(0.5, color='gray', linestyle=':', linewidth=1.0, alpha=0.6)
    ax.set_xlabel("Ordre q", fontsize=11)
    ax.set_ylabel("h(q)  [Hurst généralisé]", fontsize=11)
    ax.set_title("Comparaison h(q) — Mono vs Multifractal", fontsize=11, fontweight='bold')
    ax.legend(fontsize=9, framealpha=0.8)
    ax.grid(True, linestyle='--', alpha=0.4)
    plt.tight_layout()

    # Sauvegarde
    fig1.savefig("mfdfa_whitenoise.png",
                 dpi=150, bbox_inches='tight')
    fig2.savefig("mfdfa_multifractal.png",
                 dpi=150, bbox_inches='tight')
    fig3.savefig("mfdfa_falpha.png",
                 dpi=150, bbox_inches='tight')
    fig4.savefig("mfdfa_comparison.png",
                 dpi=150, bbox_inches='tight')

    print("\nFigures sauvegardées.")

    # ==================================================================
    # APPLICATION BTC — DONNÉES SIMULÉES RÉALISTES (2017-2024)
    # ==================================================================
    print("\n" + "=" * 65)
    print("  APPLICATION BTC/USD — Analyse Multifractale Complète")
    print("  Série journalière simulée : propriétés empiriques BTC")
    print("=" * 65)

    # ------------------------------------------------------------------
    # GÉNÉRATION DES DONNÉES BTC RÉALISTES
    # Calibration sur les propriétés empiriques documentées de BTC :
    #   - Volatilité quotidienne ≈ 4%
    #   - Kurtosis excédentaire ≈ 8–15
    #   - Asymétrie négative (crashs > rallyes)
    #   - Régimes distincts : bull 2017, bear 2018-19, COVID 2020,
    #     bull 2020-21, bear 2022, recovery 2023-24
    # ------------------------------------------------------------------
    btc_data = pd.read_csv("btc_rendements.csv", index_col=0, parse_dates=True)
    x = btc_data["rendement"].dropna().to_numpy()

    N_btc = len(x)
    scales_btc = np.unique(
        np.logspace(np.log10(10), np.log10(N_btc // 4), num=28).astype(int)
    )

    print(f"\nSérie BTC : N = {N_btc} observations (2017-2024)")
    print(f"Échelles   : [{scales_btc[0]}, {scales_btc[-1]}]  ({len(scales_btc)} points)")

    # ------------------------------------------------------------------
    # STATISTIQUES DESCRIPTIVES BTC
    # ------------------------------------------------------------------
    btc_stats = compute_descriptive_stats(x)
    print("\n--- Statistiques descriptives ---")
    for k, v in btc_stats.items():
        print(f"  {k:<30} {v}")

    # ------------------------------------------------------------------
    # MF-DFA SUR BTC
    # ------------------------------------------------------------------
    print("\nCalcul MF-DFA BTC...")
    Fq_btc = mfdfa(x, scales_btc, q_list, m=1)
    hq_btc, r2_btc = estimate_hq(scales_btc, Fq_btc, q_list)
    alpha_btc, falpha_btc, tau_btc = compute_falpha(q_list, hq_btc)

    idx_q2 = np.argmin(np.abs(q_list - 2.0))
    delta_h_btc = hq_btc[0] - hq_btc[-1]
    delta_alpha_btc = np.max(alpha_btc) - np.min(alpha_btc)

    print(f"  h(q=2)   = {hq_btc[idx_q2]:.3f}  [Hurst classique]")
    print(f"  Δh       = {delta_h_btc:.3f}  [degré de multifractalité]")
    print(f"  Δα       = {delta_alpha_btc:.3f}  [largeur spectre singularité]")
    print(f"  R² moyen = {np.mean(r2_btc):.4f}")

    # ------------------------------------------------------------------
    # TEST DE MÉLANGE — décomposition des sources de multifractalité
    # ------------------------------------------------------------------
    print("\nTest de mélange (M=30 permutations)...")
    hq_shuf, delta_h_corr, delta_h_dist = shuffling_test(
        x, scales_btc, q_list, m=1, M=30
    )
    print(f"  Δh_total  = {delta_h_btc:.3f}")
    print(f"  Δh_corr   = {delta_h_corr:.3f}  (corrélations LRC)")
    print(f"  Δh_dist   = {delta_h_dist:.3f}  (queues épaisses)")
    pct_corr = delta_h_corr / delta_h_btc * 100 if delta_h_btc > 0 else 0
    print(f"  Part corrélations : {pct_corr:.0f}%")

    # ------------------------------------------------------------------
    # VISUALISATIONS BTC COMPLÈTES
    # ------------------------------------------------------------------
    print("\nGénération des visualisations BTC...")

    

    # Fig 6 : MF-DFA BTC — scaling log-log + h(q)
    fig6 = plot_mfdfa(scales_btc, Fq_btc, q_list, hq_btc, r2_btc,
                      title="MF-DFA — BTC/USD journalier (2017–2024)")
    fig6.savefig("btc_mfdfa.png",
                 dpi=150, bbox_inches='tight')
    print("  [2/5] MF-DFA BTC — scaling + h(q) sauvegardés")

    # Fig 7 : Spectre f(α) BTC
    fig7 = plot_falpha(alpha_btc, falpha_btc,
                       title="Spectre de singularité f(α) — BTC/USD (2017–2024)")
    fig7.savefig("btc_falpha.png",
                 dpi=150, bbox_inches='tight')
    print("  [3/5] Spectre f(α) BTC sauvegardé")

    # Fig 8 : Comparaison BTC vs références + test de mélange
    fig8 = plot_btc_vs_references(q_list, hq_btc, hq_shuf,
                                   hq_wn, hq_mf, delta_h_btc,
                                   delta_h_corr, delta_h_dist)
    fig8.savefig("btc_hq_sources.png",
                 dpi=150, bbox_inches='tight')
    print("  [4/5] Décomposition sources sauvegardée")

    # Fig 9 : Tableau de bord récapitulatif
    fig9 = plot_dashboard(q_list, hq_btc, hq_wn, alpha_btc, falpha_btc,
                          tau_btc,x, btc_stats,
                          delta_h_btc, delta_h_corr, delta_h_dist)
    fig9.savefig("btc_dashboard.png",
                 dpi=150, bbox_inches='tight')
    print("  [5/5] Tableau de bord complet sauvegardé")

    print("\n" + "=" * 65)
    print("  RÉSUMÉ FINAL")
    print("=" * 65)
    print(f"  h(2) BTC      = {hq_btc[idx_q2]:.3f}  →  {'persistant (LRC)' if hq_btc[idx_q2]>0.5 else 'antipersistant'}")
    print(f"  Δh   BTC      = {delta_h_btc:.3f}  →  multifractalité {'forte' if delta_h_btc>0.3 else 'modérée'}")
    print(f"  Δα   BTC      = {delta_alpha_btc:.3f}  →  spectre {'large' if delta_alpha_btc>0.3 else 'étroit'}")
    print(f"  Part LRC      = {pct_corr:.0f}%   →  source dominante : {'corrélations' if pct_corr>50 else 'queues épaisses'}")
    print("=" * 65)