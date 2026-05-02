from __future__ import annotations

import logging
try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None

from app.models.schemas import ParsedJobDescription, ParsedResume

logger = logging.getLogger(__name__)


def match_keywords(resume: ParsedResume, jd: ParsedJobDescription) -> tuple[list[str], list[str]]:
    logger.info("Matching keywords between resume and JD.")
    resume_text = " ".join([resume.raw_text] + resume.skills).lower()
    matched: list[str] = []
    missing: list[str] = []

    for keyword in jd.required_skills:
        direct = keyword.lower() in resume_text
        fuzzy = _fuzzy_keyword_match(keyword, resume.skills)
        if direct or fuzzy:
            matched.append(keyword)
        else:
            missing.append(keyword)

    logger.debug(f"Matched {len(matched)} keywords, {len(missing)} missing.")
    return matched, missing


def _fuzzy_keyword_match(keyword: str, skills: list[str]) -> bool:
    if fuzz is not None:
        return max((fuzz.partial_ratio(keyword.lower(), skill.lower()) for skill in skills), default=0) >= 86
    keyword_lower = keyword.lower()
    return any(keyword_lower in skill.lower() or skill.lower() in keyword_lower for skill in skills)


def estimate_semantic_match(resume: ParsedResume, jd: ParsedJobDescription) -> int:
    if not resume.experience_bullets or not jd.responsibilities:
        logger.debug("Insufficient data for semantic match. Returning baseline.")
        return 45

    try:
        from sentence_transformers import SentenceTransformer, util
        logger.debug("Calculating semantic match with sentence-transformers.")

        model = SentenceTransformer("all-MiniLM-L6-v2")
        resume_vectors = model.encode(resume.experience_bullets, convert_to_tensor=True)
        jd_vectors = model.encode(jd.responsibilities, convert_to_tensor=True)
        scores = util.cos_sim(jd_vectors, resume_vectors).max(dim=1).values
        final_score = int(max(0, min(100, float(scores.mean()) * 100)))
        logger.debug(f"Semantic match score: {final_score}")
        return final_score
    except Exception as e:
        logger.warning(f"Semantic match failed: {e}. Falling back to lexical similarity.")
        return _lexical_similarity(resume, jd)


def _lexical_similarity(resume: ParsedResume, jd: ParsedJobDescription) -> int:
    resume_text = resume.raw_text.lower()
    hits = sum(1 for item in jd.responsibilities if any(word in resume_text for word in item.lower().split()[:8]))
    score = int((hits / max(1, len(jd.responsibilities))) * 100)
    logger.debug(f"Lexical similarity score: {score}")
    return score

