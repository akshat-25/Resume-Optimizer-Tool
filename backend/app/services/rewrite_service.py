from __future__ import annotations

import logging
from app.models.schemas import ParsedJobDescription, ParsedResume, Suggestion
from app.services.bullet_quality import fallback_rewrite, is_weak_bullet, sanitize_rewrite
from app.services.llm_client import OllamaClient

logger = logging.getLogger(__name__)


async def generate_llm_suggestions(
    resume: ParsedResume,
    jd: ParsedJobDescription,
    model: str,
    limit: int = 5,
) -> tuple[bool, list[Suggestion]]:
    logger.info(f"Generating LLM suggestions for up to {limit} weak bullets.")
    client = OllamaClient()
    available = await client.is_available()
    if not available:
        logger.warning("LLM suggestions requested but Ollama is not available.")
        return False, []

    suggestions: list[Suggestion] = []
    accepted_after: list[str] = []
    facts = resume.skills + resume.experience_bullets
    weak_bullets = [bullet for bullet in resume.experience_bullets if is_weak_bullet(bullet)][:limit]

    logger.debug(f"Found {len(weak_bullets)} weak bullets to rewrite.")

    for i, bullet in enumerate(weak_bullets):
        try:
            logger.debug(f"Rewriting bullet {i+1}/{len(weak_bullets)}: {bullet[:50]}...")
            result = await client.rewrite_bullet(model, bullet, facts, jd.keywords)
            after = sanitize_rewrite(bullet, result.get("after", ""), accepted_after)
            if after is None:
                logger.debug("Rewritten bullet failed sanitization. Using fallback.")
                after = fallback_rewrite(bullet)
            accepted_after.append(after)
            suggestions.append(Suggestion(
                section="Experience",
                before=bullet,
                after=after,
                why_it_is_better=result.get("why_it_is_better", "Improves specificity and role alignment."),
                needs_verification=bool(result.get("needs_verification", True)),
                questions=result.get("questions", []),
            ))
        except Exception as e:
            logger.error(f"Error generating LLM suggestion for bullet {i}: {e}")
            continue

    logger.info(f"Generated {len(suggestions)} LLM suggestions.")
    return True, suggestions

