"""
API routes for the GARCH + MF-DFA dashboard.
"""

from pathlib import Path
import io

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
import pandas as pd
import numpy as np

from api.models import AnalysisRequest, ParameterConfig
from services.analysis import run_full_analysis

router = APIRouter()

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
BTC_FILE = DATA_DIR / "btc_rendements.csv"


def get_parameter_config(
    q_min: int = Query(-5, description="Minimum q value"),
    q_max: int = Query(5, description="Maximum q value"),
    q_step: int = Query(1, ge=1, description="Step between q values"),
    min_scale: int = Query(10, ge=2, description="Minimum MF-DFA scale"),
    max_scale_divisor: int = Query(4, ge=2, description="Max scale divisor (N / divisor)"),
    m_order: int = Query(1, ge=1, description="Polynomial detrending order"),
    shuffle_iters: int = Query(20, ge=5, le=100, description="Shuffling test iterations"),
) -> ParameterConfig:
    return ParameterConfig(
        q_min=q_min,
        q_max=q_max,
        q_step=q_step,
        min_scale=min_scale,
        max_scale_divisor=max_scale_divisor,
        m_order=m_order,
        shuffle_iters=shuffle_iters,
    )


@router.get("/health")
async def health_check():
    return {"status": "ok", "message": "Backend is running"}


@router.get("/btc-data")
async def get_btc_data():
    """
    Return the bundled BTC/USD daily returns dataset (2017–2024).
    Provides prices, log-returns and dates for the descriptive plots.
    """
    if not BTC_FILE.exists():
        raise HTTPException(status_code=500, detail="BTC dataset not bundled")

    df = pd.read_csv(BTC_FILE, index_col=0, parse_dates=True)

    returns = df["rendement"].dropna().to_list()
    dates = df.index.strftime("%Y-%m-%d").to_list()
    prices = df["Prix"].dropna().to_list() if "Prix" in df.columns else None

    return {
        "name": "BTC/USD daily (2017–2024)",
        "n_observations": len(returns),
        "returns": returns,
        "prices": prices,
        "dates": dates,
        "description": "Daily Bitcoin/USD log-returns over 2017–2024.",
    }


@router.post("/analyze", response_model=dict)
async def analyze_returns(
    request: AnalysisRequest,
    params: ParameterConfig = Depends(get_parameter_config),
):
    """
    Run the full GARCH + MF-DFA + descriptive pipeline.
    Body: { returns: [...], dates: [...] }
    """
    try:
        if len(request.returns) < 100:
            raise HTTPException(status_code=400, detail="Need at least 100 observations")

        returns_array = np.array(request.returns, dtype=float)

        results = run_full_analysis(
            returns_array,
            q_min=params.q_min,
            q_max=params.q_max,
            q_step=params.q_step,
            min_scale=params.min_scale,
            max_scale_divisor=params.max_scale_divisor,
            m_order=params.m_order,
            shuffle_iters=params.shuffle_iters,
            dates=request.date_index,
        )
        return results

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload a CSV file with returns. Accepts columns:
      - returns / log_returns / rendement
      - optionally a date column ("date", "Date") or first column as index
    """
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))

        returns_col = None
        for col in ("returns", "log_returns", "rendement", "Returns", "Log_Returns"):
            if col in df.columns:
                returns_col = col
                break

        if returns_col is None:
            raise HTTPException(
                status_code=400,
                detail=("CSV must contain a column named 'returns', 'log_returns' "
                        "or 'rendement'."),
            )

        date_col = None
        for col in ("date", "Date", "dates"):
            if col in df.columns:
                date_col = col
                break

        clean = df.dropna(subset=[returns_col])
        returns = clean[returns_col].to_list()

        if date_col is not None:
            dates = pd.to_datetime(clean[date_col]).dt.strftime("%Y-%m-%d").to_list()
        else:
            try:
                dates = pd.to_datetime(clean.iloc[:, 0]).dt.strftime("%Y-%m-%d").to_list()
            except Exception:
                dates = None

        prices = None
        for col in ("Prix", "price", "Price", "Close", "close"):
            if col in df.columns:
                prices = clean[col].dropna().to_list()
                break

        return {
            "name": file.filename,
            "n_observations": len(returns),
            "returns": returns,
            "prices": prices,
            "dates": dates,
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/parameters")
async def get_default_parameters():
    """Default parameters with concise documentation."""
    return {
        "defaults": {
            "q_min": -5,
            "q_max": 5,
            "q_step": 1,
            "min_scale": 10,
            "max_scale_divisor": 4,
            "m_order": 1,
            "shuffle_iters": 20,
        },
        "explanations": {
            "q_min": "Lowest moment order. Negative q amplifies low-fluctuation segments (calm regimes).",
            "q_max": "Highest moment order. Positive q amplifies high-fluctuation segments (crisis regimes).",
            "q_step": "Spacing between consecutive q values. Smaller step = smoother h(q) curve.",
            "min_scale": "Smallest window size s used for MF-DFA. Must be >= m+2.",
            "max_scale_divisor": "Largest scale = N / divisor. Standard choice is N/4.",
            "m_order": "Polynomial order for local detrending (DFA-m). 1 removes linear trends.",
            "shuffle_iters": "Number of permutations in the shuffling test that splits Δh between LRC and heavy tails.",
        },
    }
