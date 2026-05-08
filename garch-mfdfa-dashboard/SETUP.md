# SETUP Guide

## Prerequisites

- **Docker & Docker Compose** (recommended)
- OR **Python 3.11+** & **Node.js 18+** (for direct development)

## Option 1: Docker Compose (Recommended)

### Windows
```bash
# PowerShell or Command Prompt
.\start.bat
```

### macOS / Linux
```bash
bash start.sh
```

Or manually:
```bash
docker-compose up --build
```

Services will start at:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Option 2: Local Development

### Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# OR (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app:app --reload
# Backend available at http://localhost:8000
```

### Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
# Frontend available at http://localhost:5173
```

---

## Using the Dashboard

1. **Navigate to Frontend**
   - Open http://localhost:5173 in your browser

2. **Upload Data**
   - Go to "Upload & Analyze" tab
   - Upload CSV file with returns column
   - Expected columns: `rendement`, `returns`, or `log_returns`

3. **Configure Parameters** (Optional)
   - Adjust MF-DFA parameters if needed
   - Default values work for most use cases
   - q_range: [-5, 5], scales: 25, P=1

4. **Run Analysis**
   - Click "Run Analysis" button
   - Wait for computation (1-3 mins depending on data size)
   - Results will appear in "Results" tab

5. **View Results**
   - See volatility plots (3 subplots)
   - Compare h(q) curves
   - View f(α) spectra
   - Review metrics table
   - Interpretation summary

---

## Sample Data

If you don't have data, use the included CSV files:
```bash
# From your original project
cp ../TimeSeries\ And\ Forecasting/btc_rendements.csv ./frontend/public/sample.csv
```

Then upload via dashboard.

---

## Troubleshooting

### Port Already in Use
```bash
# Check what's using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000                  # macOS/Linux

# Change ports in docker-compose.yml
# e.g., "9000:8000" for backend
```

### Build Fails
```bash
# Clear docker cache
docker-compose down
docker system prune -a
docker-compose up --build
```

### Frontend Can't Connect to Backend
- Check backend is running: `http://localhost:8000/health`
- Update API_URL in frontend `.env` if using different port
- Restart frontend after changes

---

## Next Steps

1. **Production Deployment**
   - Update docker-compose.yml with production settings
   - Deploy to AWS ECS, Heroku, DigitalOcean, etc.
   - Use environment variables for credentials

2. **Enhance Frontend**
   - Add Plotly.js for interactive charts
   - Implement result export (PDF, PNG, CSV)
   - Add historical comparison views

3. **Add Features**
   - Model parameter optimization
   - Backtesting framework
   - Real-time data streaming

---

## Development Tips

### Hot Reload
Both frontend and backend support hot reload:
- Edit `.py` files → Backend auto-reloads
- Edit `.svelte` files → Frontend auto-reloads

### Debug Mode
```bash
# Backend
PYTHONUNBUFFERED=1 uvicorn app:app --reload --log-level debug

# Frontend
npm run dev -- --debug
```

### API Testing
Use FastAPI docs at http://localhost:8000/docs (Swagger UI)

---

Enjoy your analysis! 🎉
