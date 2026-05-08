"""
MF-DFA — Multifractal Detrended Fluctuation Analysis.

Faithful re-implementation of the reference pipeline (Kantelhardt 2002):
    x -> Y(i) -> segmentation(s) -> F^2(nu, s) -> F_q(s) -> h(q)

This module mirrors the implementation used by the analysis scripts in
`TimeSeries And Forecasting/mfdfa1.py` so dashboard results match.
"""

import numpy as np


def compute_profile(x):
    """Cumulative profile Y(i) = sum_{k=1..i} (x_k - <x>)."""
    x_centered = np.asarray(x, dtype=float) - float(np.mean(x))
    return np.cumsum(x_centered)


def segment_profile(Y, s):
    """
    Two-pass segmentation: forward then backward, returning 2*N_s segments
    of length s. Backward pass starts from the tail so that no observation
    is dropped when N is not a multiple of s.
    """
    N = len(Y)
    Ns = N // s

    segments = []
    for nu in range(Ns):
        start = nu * s
        segments.append(Y[start:start + s])
    for nu in range(Ns):
        start = N - (nu + 1) * s
        segments.append(Y[start:start + s])
    return segments


def local_variance(segment, m):
    """
    Variance of residuals after a polynomial detrending of order m.
    Implements F^2(nu, s) = (1/s) * sum_i (Y(i) - y_nu(i))^2.
    """
    s = len(segment)
    i_axis = np.arange(1, s + 1, dtype=float)
    coeffs = np.polyfit(i_axis, segment, deg=m)
    trend = np.polyval(coeffs, i_axis)
    F2 = float(np.mean((segment - trend) ** 2))
    return max(F2, 1e-10)


def fluctuation_function(F2_list, q):
    """
    F_q(s) = { (1/2Ns) * sum_nu [F^2(nu,s)]^(q/2) }^(1/q),  q != 0
    F_0(s) = exp{ (1/4Ns) * sum_nu ln[F^2(nu,s)] }
    """
    F2 = np.asarray(F2_list, dtype=float)
    if abs(q) < 1e-8:
        return float(np.exp(0.5 * np.mean(np.log(F2))))
    mean_val = np.mean(F2 ** (q / 2.0))
    return float(mean_val ** (1.0 / q))


def mfdfa(x, scales, q_list, m=1):
    """
    Compute the fluctuation matrix Fq[i, j] = F_{q[i]}(scales[j]).

    Parameters
    ----------
    x : array (N,)
    scales : iterable of int (must satisfy s >= m + 2)
    q_list : iterable of float
    m : int, polynomial detrending order

    Returns
    -------
    Fq : ndarray of shape (len(q_list), len(scales))
    """
    x = np.asarray(x, dtype=float)
    Y = compute_profile(x)
    q_arr = np.asarray(q_list, dtype=float)
    scales_arr = np.asarray(scales, dtype=int)

    Fq = np.zeros((len(q_arr), len(scales_arr)))
    for j, s in enumerate(scales_arr):
        if s < m + 2:
            raise ValueError(f"Scale s={s} too small for DFA-{m}; need s >= {m + 2}.")
        segments = segment_profile(Y, int(s))
        F2_list = [local_variance(seg, m) for seg in segments]
        for i, q in enumerate(q_arr):
            Fq[i, j] = fluctuation_function(F2_list, q)
    return Fq


def estimate_hq(scales, Fq, q_list):
    """Estimate h(q) by log-log regression of F_q(s) on s. Also returns R²."""
    log_s = np.log(np.asarray(scales, dtype=float))
    q_arr = np.asarray(q_list, dtype=float)

    hq = np.zeros(len(q_arr))
    r2 = np.zeros(len(q_arr))
    for i in range(len(q_arr)):
        log_Fq = np.log(Fq[i, :])
        coeffs = np.polyfit(log_s, log_Fq, deg=1)
        hq[i] = coeffs[0]
        log_Fq_fit = np.polyval(coeffs, log_s)
        ss_res = np.sum((log_Fq - log_Fq_fit) ** 2)
        ss_tot = np.sum((log_Fq - np.mean(log_Fq)) ** 2)
        r2[i] = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    return hq, r2


def compute_falpha(q_list, hq):
    """
    Singularity spectrum f(α) via Legendre transform.
        tau(q) = q*h(q) - 1
        alpha  = h(q) + q * h'(q)
        f(α)   = q * (alpha - h(q)) + 1
    """
    q = np.asarray(q_list, dtype=float)
    h = np.asarray(hq, dtype=float)

    tau = q * h - 1.0
    dh = np.gradient(h, q)
    alpha = h + q * dh
    falpha = q * (alpha - h) + 1.0
    return alpha, falpha, tau
