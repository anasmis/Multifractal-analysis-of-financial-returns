"""
Analysis service: GARCH fitting + MF-DFA computation + descriptive statistics
+ shuffling test (multifractality source decomposition) + reference series.
"""

import numpy as np
import warnings
from arch import arch_model
from scipy import stats as sp_stats
from .mfdfa import mfdfa, estimate_hq, compute_falpha

warnings.filterwarnings('ignore')


def _json_safe(value):
    """Convert numpy/pandas values to JSON-safe Python values."""
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return [_json_safe(item) for item in value.tolist()]
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return None if not np.isfinite(number) else number
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if value is None:
        return None
    return value


def fit_garch_model(returns_pct, vol_type='GARCH', p=1, q=1, dist='t'):
    """Fit GARCH/EGARCH/FIGARCH model. Returns (result, std_resid, cond_vol)."""
    try:
        if vol_type == 'FIGARCH':
            am = arch_model(returns_pct, mean='Constant', vol='FIGARCH',
                            p=p, q=q, dist=dist)
        elif vol_type == 'EGARCH':
            am = arch_model(returns_pct, mean='Constant', vol='EGARCH',
                            p=p, o=1, q=q, dist=dist)
        else:
            am = arch_model(returns_pct, mean='Constant', vol='GARCH',
                            p=p, q=q, dist=dist)

        res = am.fit(disp='off', options={'maxiter': 500})
        std_resid = np.asarray(res.std_resid)
        cond_vol = np.asarray(res.conditional_volatility)
        return res, std_resid, cond_vol
    except Exception as exc:
        print(f"Error fitting {vol_type}: {exc}")
        return None, None, None


def get_persistence(res, vol_type):
    """Extract persistence parameter from a fitted model."""
    try:
        params = res.params
        if vol_type == 'GARCH':
            return float(params.get('alpha[1]', 0) + params.get('beta[1]', 0))
        if vol_type == 'EGARCH':
            return float(params.get('beta[1]', 0))
        return float(params.get('d', np.nan))
    except Exception:
        return float('nan')


def compute_descriptive_stats(returns):
    """Full descriptive statistics block (mirrors the analysis script)."""
    r = np.asarray(returns, dtype=float)
    mu = float(np.mean(r))
    sigma = float(np.std(r, ddof=1))
    skew = float(sp_stats.skew(r))
    kurt = float(sp_stats.kurtosis(r))  # excess kurtosis
    jb = sp_stats.jarque_bera(r)
    jb_stat = float(jb.statistic)
    jb_pval = float(jb.pvalue)

    abs_r = np.abs(r - mu)
    acf1 = float(np.corrcoef(abs_r[:-1], abs_r[1:])[0, 1])
    acf5 = float(np.corrcoef(abs_r[:-5], abs_r[5:])[0, 1]) if len(r) > 6 else float('nan')
    acf20 = float(np.corrcoef(abs_r[:-20], abs_r[20:])[0, 1]) if len(r) > 21 else float('nan')

    # ACF of squared returns (ARCH effect)
    max_lag = 30
    acf_sq = []
    r_sq = (r - mu) ** 2
    for k in range(1, max_lag + 1):
        denom = np.sum((r_sq - r_sq.mean()) ** 2)
        if denom <= 0 or k >= len(r_sq):
            acf_sq.append(0.0)
        else:
            num = np.sum((r_sq[:-k] - r_sq.mean()) * (r_sq[k:] - r_sq.mean()))
            acf_sq.append(float(num / denom))

    # ACF of |r| (memory in volatility)
    max_lag_abs = 100
    acf_abs = []
    abs_centered = abs_r - abs_r.mean()
    denom_abs = np.sum(abs_centered ** 2)
    for k in range(1, max_lag_abs + 1):
        if k >= len(abs_r) or denom_abs <= 0:
            acf_abs.append(0.0)
        else:
            num = np.sum(abs_centered[:-k] * abs_centered[k:])
            acf_abs.append(float(num / denom_abs))

    n = len(r)
    ci95 = float(1.96 / np.sqrt(n)) if n > 0 else 0.0

    annualized = float(sigma * np.sqrt(252) * 100)

    pct_pos = float(np.mean(r > 0) * 100)
    pct_neg = float(np.mean(r < 0) * 100)

    return {
        "n_observations": int(n),
        "mean": mu,
        "std": sigma,
        "annualized_vol_pct": annualized,
        "min": float(r.min()),
        "max": float(r.max()),
        "skewness": skew,
        "excess_kurtosis": kurt,
        "jarque_bera_stat": jb_stat,
        "jarque_bera_pvalue": jb_pval,
        "is_non_normal": bool(jb_pval < 0.05),
        "acf_abs_lag1": acf1,
        "acf_abs_lag5": acf5,
        "acf_abs_lag20": acf20,
        "pct_positive_days": pct_pos,
        "pct_negative_days": pct_neg,
        "acf_squared": acf_sq,
        "acf_abs": acf_abs,
        "acf_ci95": ci95,
        "histogram_returns": _histogram(r, bins=80),
        "qq_plot": _qq_plot_points(r),
    }


def _histogram(values, bins=80):
    """Pre-computed histogram as (centers, density) for the frontend."""
    counts, edges = np.histogram(values, bins=bins, density=True)
    centers = (edges[:-1] + edges[1:]) / 2
    return {
        "centers": centers.tolist(),
        "density": counts.tolist(),
        "mean": float(np.mean(values)),
        "std": float(np.std(values, ddof=1)),
    }


def _qq_plot_points(values, max_points=400):
    """Theoretical quantiles vs empirical for a Normal QQ-plot."""
    (osm, osr), (slope, intercept, _) = sp_stats.probplot(values, dist="norm")
    if len(osm) > max_points:
        idx = np.linspace(0, len(osm) - 1, max_points).astype(int)
        osm = osm[idx]
        osr = osr[idx]
    return {
        "theoretical": np.asarray(osm).tolist(),
        "empirical": np.asarray(osr).tolist(),
        "slope": float(slope),
        "intercept": float(intercept),
    }


def run_mfdfa(x, scales, q, m_order, label=""):
    """Helper to run MF-DFA and compute multifractal metrics."""
    Fq = mfdfa(x, scales, q, m_order)
    hq, r2 = estimate_hq(scales, Fq, q)
    al, fa, tau = compute_falpha(q, hq)
    dh = float(hq[0] - hq[-1])
    al_clean = al[np.isfinite(al)]
    da = float(np.nanmax(al_clean) - np.nanmin(al_clean)) if al_clean.size else float('nan')
    if label:
        print(f"  {label:<22} dh={dh:.3f}  da={da:.3f}")
    return {
        "Fq": Fq,
        "hq": hq,
        "r2": r2,
        "alpha": al,
        "falpha": fa,
        "tau_q": tau,
        "delta_h": dh,
        "delta_alpha": da,
    }


def shuffling_test(returns, scales, q, m_order=1, M=20, seed=42):
    """
    Test de mélange (Kantelhardt 2002, Eq. 28).
    Décompose Δh_total = Δh_corr (LRC) + Δh_dist (queues).
    """
    rng = np.random.default_rng(seed)
    hq_shuf_all = np.zeros((M, len(q)))
    for k in range(M):
        x_perm = rng.permutation(returns)
        Fq_p = mfdfa(x_perm, scales, q, m_order)
        hq_p, _ = estimate_hq(scales, Fq_p, q)
        hq_shuf_all[k] = hq_p

    hq_shuf = np.nanmean(hq_shuf_all, axis=0)
    Fq_orig = mfdfa(returns, scales, q, m_order)
    hq_orig, _ = estimate_hq(scales, Fq_orig, q)

    delta_h_total = float(hq_orig[0] - hq_orig[-1])
    delta_h_dist = float(hq_shuf[0] - hq_shuf[-1])
    delta_h_corr = float(delta_h_total - delta_h_dist)

    return {
        "hq_original": hq_orig.tolist(),
        "hq_shuffled": hq_shuf.tolist(),
        "delta_h_total": delta_h_total,
        "delta_h_corr": delta_h_corr,
        "delta_h_dist": delta_h_dist,
        "pct_corr": float(delta_h_corr / delta_h_total * 100) if delta_h_total > 0 else 0.0,
        "q_values": np.asarray(q, dtype=float).tolist(),
    }


def generate_white_noise(N=2048, seed=42):
    rng = np.random.default_rng(seed)
    return rng.standard_normal(N)


def generate_fbm(N=2048, H=0.75, seed=42):
    """Approximate fractional Brownian motion increments."""
    rng = np.random.default_rng(seed)
    f = np.fft.rfftfreq(N)[1:]
    power = f ** (-(2 * H + 1) / 2)
    phases = rng.uniform(0, 2 * np.pi, len(f))
    spectrum = np.zeros(N // 2 + 1, dtype=complex)
    spectrum[1:] = power * np.exp(1j * phases)
    x = np.fft.irfft(spectrum, n=N)
    x = np.diff(x)
    return x / x.std()


def generate_binomial_cascade(N=2048, a=0.6, seed=42):
    """Multiplicative binomial cascade — multifractal."""
    rng = np.random.default_rng(seed)
    n_levels = int(np.log2(N))
    measure = np.ones(1)
    for _ in range(n_levels):
        new_m = np.empty(len(measure) * 2)
        new_m[0::2] = measure * a
        new_m[1::2] = measure * (1 - a)
        measure = new_m
    measure = measure[:N]
    x = measure + 0.01 * rng.standard_normal(N)
    return x / np.std(x)


def compute_reference_hq(scales, q, m_order=1, N=2048, seed=42):
    """Compute h(q) for the three reference series used as benchmarks."""
    Q = np.asarray(q, dtype=float)
    refs = {}
    for name, x in [
        ("white_noise", generate_white_noise(N, seed)),
        ("fbm", generate_fbm(N, 0.75, seed)),
        ("binomial_cascade", generate_binomial_cascade(N, 0.6, seed)),
    ]:
        Fq = mfdfa(x, scales, Q, m_order)
        hq, _ = estimate_hq(scales, Fq, Q)
        refs[name] = {
            "hq": hq.tolist(),
            "delta_h": float(hq[0] - hq[-1]),
            "h_q2": float(hq[np.argmin(np.abs(Q - 2))]),
        }
    return refs


def compute_ccdf(returns, max_points=400):
    """Sorted |r| and empirical CCDF, plus a power-law fit on the upper tail."""
    abs_r = np.abs(np.asarray(returns, dtype=float))
    sorted_desc = np.sort(abs_r)[::-1]
    n = len(sorted_desc)
    ccdf = np.arange(1, n + 1) / n

    # Subsample for transmission
    if n > max_points:
        idx = np.unique(np.linspace(0, n - 1, max_points).astype(int))
        x_out = sorted_desc[idx]
        y_out = ccdf[idx]
    else:
        x_out = sorted_desc
        y_out = ccdf

    nu_hat = None
    fit_x = None
    fit_y = None
    threshold = float(np.percentile(abs_r, 85))
    mask = sorted_desc > threshold
    if mask.sum() > 20:
        lx = np.log(sorted_desc[mask])
        ly = np.log(ccdf[mask])
        coef = np.polyfit(lx, ly, 1)
        nu_hat = float(-coef[0])
        # Build fit line on the full upper-tail support
        fit_x_arr = sorted_desc[mask]
        fit_y_arr = np.exp(coef[1]) * fit_x_arr ** coef[0]
        # subsample
        if len(fit_x_arr) > max_points:
            idx = np.unique(np.linspace(0, len(fit_x_arr) - 1, max_points).astype(int))
            fit_x_arr = fit_x_arr[idx]
            fit_y_arr = fit_y_arr[idx]
        fit_x = fit_x_arr.tolist()
        fit_y = fit_y_arr.tolist()

    return {
        "x": x_out.tolist(),
        "y": y_out.tolist(),
        "nu_hat": nu_hat,
        "threshold": threshold,
        "fit_x": fit_x,
        "fit_y": fit_y,
    }


def run_full_analysis(returns, q_min=-5, q_max=5, q_step=1,
                      min_scale=10, max_scale_divisor=4, m_order=1,
                      shuffle_iters=20, dates=None):
    """Complete GARCH + MF-DFA + descriptive analysis pipeline."""
    Q = np.arange(q_min, q_max + 1, q_step, dtype=float)
    N = len(returns)
    SCALES = np.unique(np.logspace(
        np.log10(min_scale),
        np.log10(N // max_scale_divisor),
        25
    ).astype(int))

    r_pct = np.asarray(returns, dtype=float) * 100

    # 1. Descriptive
    print("Descriptive statistics...")
    descriptive = compute_descriptive_stats(returns)

    # 2. GARCH family
    print("Fitting GARCH(1,1)...")
    res_garch, z_garch, vol_garch = fit_garch_model(r_pct, 'GARCH')
    print("Fitting EGARCH(1,1)...")
    res_egarch, z_egarch, vol_egarch = fit_garch_model(r_pct, 'EGARCH')
    print("Fitting FIGARCH(1,d,1)...")
    res_figarch, z_figarch, vol_figarch = fit_garch_model(r_pct, 'FIGARCH')

    # 3. MF-DFA
    print("MF-DFA — original series...")
    mf_orig = run_mfdfa(np.asarray(returns), SCALES, Q, m_order, "Original")
    print("MF-DFA — GARCH residuals...")
    mf_g = run_mfdfa(z_garch, SCALES, Q, m_order, "GARCH residuals")
    print("MF-DFA — EGARCH residuals...")
    mf_eg = run_mfdfa(z_egarch, SCALES, Q, m_order, "EGARCH residuals")
    print("MF-DFA — FIGARCH residuals...")
    mf_fig = run_mfdfa(z_figarch, SCALES, Q, m_order, "FIGARCH residuals")

    # 4. Shuffling test
    print(f"Shuffling test (M={shuffle_iters})...")
    shuffle = shuffling_test(np.asarray(returns), SCALES, Q, m_order, M=shuffle_iters)

    # 5. Reference benchmarks (white noise, fBm, binomial cascade)
    print("Reference benchmarks...")
    references = compute_reference_hq(SCALES, Q, m_order, N=min(N, 2048))

    # 6. Heavy tails CCDF
    ccdf = compute_ccdf(returns)

    # 7. Best-model summary
    best_aic = min([
        ("GARCH", float(res_garch.aic)),
        ("EGARCH", float(res_egarch.aic)),
        ("FIGARCH", float(res_figarch.aic)),
    ], key=lambda item: item[1])
    best_mf = min([
        ("GARCH", mf_g["delta_h"]),
        ("EGARCH", mf_eg["delta_h"]),
        ("FIGARCH", mf_fig["delta_h"]),
    ], key=lambda item: item[1])

    def make_interpretation(dh_orig, dh_resid, da_orig, da_resid):
        red_dh = (dh_orig - dh_resid) / dh_orig * 100 if dh_orig else 0.0
        red_da = (da_orig - da_resid) / da_orig * 100 if da_orig else 0.0
        persistent = dh_resid > 0.10
        return {
            "delta_h_reduction": red_dh,
            "delta_alpha_reduction": red_da,
            "multifractal_persistent": persistent,
            "message": ("Multifractalité persistante — complexité non capturée"
                        if persistent else
                        "Multifractalité largement absorbée"),
        }

    interpretation = {
        "GARCH": make_interpretation(mf_orig["delta_h"], mf_g["delta_h"],
                                     mf_orig["delta_alpha"], mf_g["delta_alpha"]),
        "EGARCH": make_interpretation(mf_orig["delta_h"], mf_eg["delta_h"],
                                      mf_orig["delta_alpha"], mf_eg["delta_alpha"]),
        "FIGARCH": make_interpretation(mf_orig["delta_h"], mf_fig["delta_h"],
                                       mf_orig["delta_alpha"], mf_fig["delta_alpha"]),
    }

    idx_q2 = int(np.argmin(np.abs(Q - 2)))

    # Stride for time series transmission
    def _stride(arr, target=1500):
        a = np.asarray(arr)
        if a.size <= target:
            return a.tolist()
        step = max(1, a.size // target)
        return a[::step].tolist()

    results = {
        "n_observations": int(N),
        "scales": SCALES.tolist(),
        "q_values": Q.tolist(),
        "dates": dates if dates else None,

        "returns": _stride(returns, 2600),

        "descriptive": descriptive,

        "original_metrics": {
            "model_name": "Original returns",
            "aic": None, "bic": None, "log_likelihood": None, "persistence": None,
            "delta_h": mf_orig["delta_h"],
            "delta_alpha": mf_orig["delta_alpha"],
            "h_q2": float(mf_orig["hq"][idx_q2]),
            "params": {},
        },
        "original_mfdfa": {
            "hq": mf_orig["hq"].tolist(),
            "tau_q": mf_orig["tau_q"].tolist(),
            "alpha": mf_orig["alpha"].tolist(),
            "falpha": mf_orig["falpha"].tolist(),
            "q_values": Q.tolist(),
            "r2_mean": float(np.nanmean(mf_orig["r2"])),
        },

        "garch_metrics": {
            "model_name": "GARCH(1,1)-t",
            "aic": float(res_garch.aic),
            "bic": float(res_garch.bic),
            "log_likelihood": float(res_garch.loglikelihood),
            "persistence": get_persistence(res_garch, 'GARCH'),
            "delta_h": mf_g["delta_h"],
            "delta_alpha": mf_g["delta_alpha"],
            "h_q2": float(mf_g["hq"][idx_q2]),
            "params": {k: float(v) for k, v in res_garch.params.items()},
        },
        "garch_mfdfa": {
            "hq": mf_g["hq"].tolist(),
            "tau_q": mf_g["tau_q"].tolist(),
            "alpha": mf_g["alpha"].tolist(),
            "falpha": mf_g["falpha"].tolist(),
            "q_values": Q.tolist(),
        },

        "egarch_metrics": {
            "model_name": "EGARCH(1,1)-t",
            "aic": float(res_egarch.aic),
            "bic": float(res_egarch.bic),
            "log_likelihood": float(res_egarch.loglikelihood),
            "persistence": get_persistence(res_egarch, 'EGARCH'),
            "delta_h": mf_eg["delta_h"],
            "delta_alpha": mf_eg["delta_alpha"],
            "h_q2": float(mf_eg["hq"][idx_q2]),
            "params": {k: float(v) for k, v in res_egarch.params.items()},
        },
        "egarch_mfdfa": {
            "hq": mf_eg["hq"].tolist(),
            "tau_q": mf_eg["tau_q"].tolist(),
            "alpha": mf_eg["alpha"].tolist(),
            "falpha": mf_eg["falpha"].tolist(),
            "q_values": Q.tolist(),
        },

        "figarch_metrics": {
            "model_name": "FIGARCH(1,d,1)-t",
            "aic": float(res_figarch.aic),
            "bic": float(res_figarch.bic),
            "log_likelihood": float(res_figarch.loglikelihood),
            "persistence": get_persistence(res_figarch, 'FIGARCH'),
            "delta_h": mf_fig["delta_h"],
            "delta_alpha": mf_fig["delta_alpha"],
            "h_q2": float(mf_fig["hq"][idx_q2]),
            "params": {k: float(v) for k, v in res_figarch.params.items()},
        },
        "figarch_mfdfa": {
            "hq": mf_fig["hq"].tolist(),
            "tau_q": mf_fig["tau_q"].tolist(),
            "alpha": mf_fig["alpha"].tolist(),
            "falpha": mf_fig["falpha"].tolist(),
            "q_values": Q.tolist(),
        },

        "conditional_volatility": {
            "GARCH": _stride(vol_garch, 2600),
            "EGARCH": _stride(vol_egarch, 2600),
            "FIGARCH": _stride(vol_figarch, 2600),
        },

        "shuffle": shuffle,
        "references": references,
        "ccdf": ccdf,

        "best_model_aic": best_aic[0],
        "best_model_mf_reduction": best_mf[0],
        "interpretation": interpretation,
    }

    return _json_safe(results)
