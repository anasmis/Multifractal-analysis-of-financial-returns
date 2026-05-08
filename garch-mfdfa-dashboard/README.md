# GARCH + MF-DFA Analysis Dashboard

A full-featured web application for comparing GARCH, EGARCH, and FIGARCH models with Multifractal Detrended Fluctuation Analysis (MF-DFA) on financial time series data.

## 🎯 Features

- **Model Comparison**: GARCH(1,1), EGARCH(1,1), FIGARCH(1,d,1) with Student-t distributions
- **Multifractal Analysis**: MF-DFA with configurable q-range and scaling parameters
- **Interactive Dashboard**: 
  - CSV file upload with automatic encoding
  - Parameter tuning interface
  - Real-time analysis with progress indicators
  - Model metrics comparison table
  - Interactive visualization plots
- **Results Export**: Download analysis results and visualizations
- **Cloud Deployment Ready**: Docker Compose for local + cloud deployments

## 📊 Project Structure

```
garch-mfdfa-dashboard/
├── backend/                      # FastAPI server
│   ├── app.py                    # Main FastAPI app
│   ├── requirements.txt          # Python dependencies
│   ├── api/
│   │   ├── models.py            # Pydantic request/response models
│   │   └── routes.py            # API endpoints
│   ├── services/
│   │   ├── mfdfa.py            # MF-DFA implementation
│   │   └── analysis.py         # GARCH fitting + analysis
│   ├── Dockerfile              # Backend container
│   └── .gitignore
├── frontend/                     # Svelte web app
│   ├── src/
│   │   ├── App.svelte          # Main app component
│   │   ├── main.js             # Entry point
│   │   ├── components/         # Reusable components
│   │   │   ├── Dashboard.svelte
│   │   │   ├── FileUpload.svelte
│   │   │   ├── ParameterPanel.svelte
│   │   │   ├── PlotGrid.svelte
│   │   │   └── ResultsTable.svelte
│   │   └── stores/
│   │       └── analysis.js    # Svelte state management
│   ├── package.json           # NPM dependencies
│   ├── vite.config.js         # Vite build config
│   ├── svelte.config.js       # Svelte config
│   ├── index.html             # HTML entry point
│   ├── Dockerfile             # Frontend container
│   └── .gitignore
├── docker-compose.yml          # Multi-container orchestration
└── README.md
```

## 🚀 Quick Start

### Local Development (with Docker Compose)

1. **Requirements**:
   - Docker & Docker Compose
   - Node.js 18+ (optional, for direct npm development)
   - Python 3.11+ (optional, for direct backend development)

2. **Setup**:
```bash
cd garch-mfdfa-dashboard

# Start all services
docker-compose up

# Services available at:
# - Frontend: http://localhost:5173
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

3. **Upload Data**:
   - Prepare CSV with returns column (`returns`, `log_returns`, or `rendement`)
   - Upload via dashboard
   - Configure MF-DFA parameters (optional)
   - Click "Run Analysis"

4. **View Results**:
   - Volatility plots (GARCH, EGARCH, FIGARCH)
   - h(q) comparison (Hurst generalized)
   - f(α) spectra (singularity spectra)
   - Multifractal metrics summary

### Local Development (without Docker)

**Backend**:
```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload
# Backend at http://localhost:8000
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev
# Frontend at http://localhost:5173
```

## 📡 API Endpoints

### `POST /upload`
Upload CSV file with returns data
```bash
curl -F "file=@btc_rendements.csv" http://localhost:8000/upload
```

### `POST /analyze`
Run GARCH + MF-DFA analysis
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "returns": [0.001, 0.002, ...],
    "model_type": "all"
  }'
```

### `GET /parameters`
Get default MF-DFA parameters
```bash
curl http://localhost:8000/parameters
```

### `GET /health`
Health check
```bash
curl http://localhost:8000/health
```

## 🔧 Configuration

### MF-DFA Parameters
- **q_min / q_max**: Range of moments (default: -5 to 5)
- **q_step**: Step size (default: 1)
- **min_scale**: Minimum scale for analysis (default: 10)
- **max_scale_divisor**: N / divisor = max scale (default: 4)
- **m_order**: Polynomial order for detrending (default: 1 = DFA1)

### Expected CSV Format
```csv
date,rendement
2017-01-01,0.001234
2017-01-02,-0.000567
...
```

Column names recognized: `rendement`, `returns`, `log_returns`

## 📊 Output Metrics

For each model (GARCH, EGARCH, FIGARCH):
- **AIC / BIC**: Information criteria
- **Log-Likelihood**: Model fit quality
- **Δh**: Multifractal amplitude (h_min - h_max)
- **Δα**: Singularity spectrum width
- **h(2)**: Classical Hurst exponent
- **Persistence**: Model-specific persistence metric

### Interpretation
- **Δh close to 0**: Monofractal behavior (random walk)
- **Δh > 0.15**: Strong multifractal structure
- Residual Δh after filtering: Complexity not captured by the model

## 🐳 Docker Deployment

### Build Custom Images
```bash
docker build -t garch-backend:latest ./backend
docker build -t garch-frontend:latest ./frontend
```

### Cloud Deployment (AWS ECS, Heroku, etc.)
1. Push images to registry (ECR, Docker Hub, etc.)
2. Update docker-compose.yml with image URIs
3. Deploy to cloud platform

### Environment Variables
```bash
# backend/.env
PYTHONUNBUFFERED=1
LOG_LEVEL=INFO

# frontend/.env
VITE_API_URL=https://api.example.com
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm run test
```

## 📝 Model Details

### GARCH(1,1)-t
- Constant mean + GARCH volatility
- Student-t distribution (heavy tails)
- Parameters: α, β (ARCH/GARCH effects)

### EGARCH(1,1)-t
- Exponential GARCH (asymmetric response)
- Student-t distribution
- Captures leverage effects

### FIGARCH(1,d,1)-t
- Fractionally Integrated GARCH
- Long-memory in conditional variance
- Parameter d: memory strength (0 < d < 1)

## 🔬 MF-DFA Methodology

1. **Profile**: Y(i) = Σ [x_t - mean(x)]
2. **Segmentation**: Divide into non-overlapping segments
3. **Detrending**: Fit polynomial, compute residuals
4. **Fluctuation**: F_q(s) = [avg(F²(segment))^(q/2)]^(1/q)
5. **Scaling**: h(q) from log-log regression of F_q vs scale
6. **Singularity Spectrum**: f(α) from Legendre transform of τ(q)

## 📚 References

- Kantelhardt et al. (2002): Multifractal Detrended Fluctuation Analysis
- Nelson (1991): Conditional Heteroskedasticity in Asset Returns
- Baillie et al. (1996): Long Memory and Forecasting

## 📄 License

MIT License

## 👤 Author

Created for Time Series & Forecasting course

## 🤝 Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## 📧 Support

For issues, questions, or suggestions:
- Open GitHub issue
- Contact: [your-email]

---

**Happy Analyzing!** 📈✨
