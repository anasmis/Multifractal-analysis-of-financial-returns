"""
FastAPI main application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router

# Initialize app
app = FastAPI(
    title="GARCH + MF-DFA Analysis API",
    description="Compare GARCH, EGARCH, FIGARCH models with multifractal analysis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, tags=["analysis"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "GARCH + MF-DFA Analysis API",
        "docs": "/docs",
        "health": "/health"
    }
