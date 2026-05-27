import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .config import get_settings
from .db.mongodb import init_db, close_db
from .api.routes import health, claims, decisions
from .api.middleware import LoggingMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up Claims Processor...")
    try:
        await init_db()
        logger.info("Database connected")
    except Exception as e:
        logger.warning(f"Database connection failed: {e}. Running without persistence.")
    
    yield
    
    logger.info("Shutting down...")
    await close_db()


app = FastAPI(
    title="Health Insurance Claims Processor",
    description="Multi-agent system for processing health insurance claims",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)

app.include_router(health.router, prefix="/api")
app.include_router(claims.router, prefix="/api")
app.include_router(decisions.router, prefix="/api")

frontend_path = Path(__file__).parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


@app.get("/api")
async def root():
    return {
        "message": "Health Insurance Claims Processor API",
        "docs": "/docs",
        "health": "/api/health"
    }
