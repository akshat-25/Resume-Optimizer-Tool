
import asyncio
import json
import logging
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)

try:
    import httpx
except ImportError:
    httpx = None
    logger.warning("httpx not found. Using urllib fallback for OllamaClient.")


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self.base_url = base_url

    async def is_available(self) -> bool:
        logger.debug(f"Checking if Ollama is available at {self.base_url}")
        try:
            if httpx is None:
                await asyncio.to_thread(_json_request, f"{self.base_url}/api/tags")
                return True
            async with httpx.AsyncClient(timeout=2) as client:
                response = await client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            return False

    async def list_models(self) -> list[str]:
        logger.info("Listing local Ollama models.")
        try:
            if httpx is None:
                data = await asyncio.to_thread(_json_request, f"{self.base_url}/api/tags")
                return [model["name"] for model in data.get("models", [])]

            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            logger.debug(f"Found models: {models}")
            return models
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []

    async def rewrite_bullet(self, model: str, bullet: str, resume_facts: list[str], jd_keywords: list[str]) -> dict:
        logger.info(f"Requesting bullet rewrite from model {model}.")
        prompt = f"""
You improve exactly one resume bullet while preserving truth.
Rules:
- Rewrite only the original bullet. Do not rewrite job titles, company names, dates, or locations.
- Use only facts in the original bullet. Resume facts are context only, not permission to merge multiple bullets.
- Do not invent numbers, companies, dates, tools, degrees, or certifications.
- Do not add technologies unless they already appear in the original bullet.
- Keep the rewritten bullet under 35 words.
- Return one concise resume bullet, not a paragraph.
- Return JSON only with keys: after, why_it_is_better, needs_verification, questions.

Original bullet:
{bullet}

Resume facts:
{resume_facts[:30]}

Relevant job keywords:
{jd_keywords[:20]}
"""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1, "num_predict": 180},
        }
        if httpx is None:
            data = await asyncio.to_thread(_json_request, f"{self.base_url}/api/generate", payload, 120)
            return json.loads(data.get("response", "{}"))

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()
        raw = response.json().get("response", "{}")
        return json.loads(raw)


def _json_request(url: str, payload: dict | None = None, timeout: int = 5) -> dict:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method="POST" if payload else "GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(str(exc)) from exc
