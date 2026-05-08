"""
Pydantic models for request/response validation.
"""

from typing import List, Optional
from pydantic import BaseModel


class AnalysisRequest(BaseModel):
    """Request body for GARCH + MF-DFA analysis."""
    model_config = {
        "protected_namespaces": (),
    }

    returns: List[float]  # log-returns data
    model_type: Optional[str] = "all"  # "GARCH", "EGARCH", "FIGARCH", or "all"
    date_index: Optional[List[str]] = None  # ISO dates for x-axis labels


class ParameterConfig(BaseModel):
    """MF-DFA parameter configuration."""
    q_min: int = -5
    q_max: int = 5
    q_step: int = 1
    min_scale: int = 10
    max_scale_divisor: int = 4
    m_order: int = 1  # DFA order
    shuffle_iters: int = 20  # number of permutations for the shuffling test


class MetricsResponse(BaseModel):
    """Response containing computed metrics."""
    model_config = {
        "protected_namespaces": (),
    }

    model_name: str
    aic: float
    bic: float
    log_likelihood: float
    persistence: float
    delta_h: float
    delta_alpha: float
    h_q2: float  # h(q=2)
    params: dict  # User's estimated parameters


class MFDFAResults(BaseModel):
    """MF-DFA analysis results."""
    hq: List[float]  # h(q) values
    tau_q: List[float]  # τ(q) values
    alpha: List[float]  # Hölder exponents
    falpha: List[float]  # f(α) dimensions
    q_values: List[float]  # q range


class ChartData(BaseModel):
    """Data for frontend plots."""
    name: str
    x: List[float]
    y: List[float]
    type: str  # "line", "bar", "scatter"
    color: str


class AnalysisResponse(BaseModel):
    """Complete analysis response."""
    original_metrics: MetricsResponse  # BTC original
    garch_metrics: MetricsResponse
    garch_mfdfa: MFDFAResults
    garch_residuals: Optional[List[float]] = None
    
    egarch_metrics: MetricsResponse
    egarch_mfdfa: MFDFAResults
    egarch_residuals: Optional[List[float]] = None
    
    figarch_metrics: MetricsResponse
    figarch_mfdfa: MFDFAResults
    figarch_residuals: Optional[List[float]] = None
    
    # Timeseries for plots
    conditional_volatility: dict  # {"GARCH": [...], "EGARCH": [...], "FIGARCH": [...]}
    
    # Interpretation
    best_model_aic: str
    best_model_mf_reduction: str
    interpretation: dict  # {"GARCH": {...}, "EGARCH": {...}, "FIGARCH": {...}}
