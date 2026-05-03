
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analysis_routes import router as analysis_router
from app.api.model_routes import router as model_router

app = FastAPI(title="Resume Tailor API", version="0.1.0")
logger.info("Resume Tailor API started")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200", "http://localhost:65357"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis_router, prefix="/api")
app.include_router(model_router, prefix="/api")


@app.get("/api/health")
async def health() -> dict[str, str]:
    logger.info("Health check endpoint called")
    return {"status": "ok"}
