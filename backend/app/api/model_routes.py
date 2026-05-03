import logging

logger = logging.getLogger(__name__)

from fastapi import APIRouter

from app.services.llm_client import OllamaClient

router = APIRouter(tags=["models"])


@router.get("/models/local")
async def local_models() -> dict:
    logger.info("Checking local models availability.")
    client = OllamaClient()
    available = await client.is_available()
    if not available:
        logger.warning("Ollama client not available. Returning recommended models.")
        return {
            "available": False,
            "recommended": ["qwen3:8b", "gemma3:4b", "gemma3:12b"],
            "models": [],
        }
    logger.info("Ollama client available. Listing local models.")
    models = await client.list_models()
    logger.info(f"Found {len(models)} local models.")
    return {
        "available": True,
        "recommended": ["qwen3:8b", "gemma3:4b", "gemma3:12b"],
        "models": models,
    }
