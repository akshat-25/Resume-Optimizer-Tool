
import logging
import re

from app.models.schemas import ParsedJobDescription, ParsedResume, ScoreBreakdown

logger = logging.getLogger(__name__)


def score_resume(
    resume: ParsedResume,
    jd: ParsedJobDescription,
    matched_keywords: list[str],
    semantic_match: int,
    ats_score: int,
) -> ScoreBreakdown:
    logger.info("Calculating resume scores.")
    keyword_score = int((len(matched_keywords) / max(1, len(jd.required_skills))) * 100)
    impact_score = _impact_score(resume.experience_bullets)
    clarity_score = _clarity_score(resume)
    completeness = _completeness_score(resume)
    experience_relevance = int((semantic_match + keyword_score) / 2)

    overall = int(
        keyword_score * 0.25
        + semantic_match * 0.20
        + experience_relevance * 0.15
        + ats_score * 0.15
        + impact_score * 0.10
        + clarity_score * 0.10
        + completeness * 0.05
    )

    logger.debug(f"Scores - Overall: {overall}, Keywords: {keyword_score}, Semantic: {semantic_match}, ATS: {ats_score}")

    return ScoreBreakdown(
        overall=overall,
        ats=ats_score,
        keyword_match=keyword_score,
        semantic_match=semantic_match,
        impact=impact_score,
        clarity=clarity_score,
        completeness=completeness,
    )



def _impact_score(bullets: list[str]) -> int:
    if not bullets:
        return 35
    strong = 0
    for bullet in bullets:
        has_action = re.search(r"\b(built|developed|designed|led|launched|optimized|reduced|increased|automated|improved)\b", bullet, re.I)
        has_metric = re.search(r"\d+%?|\b(thousand|million|users|requests|latency|revenue)\b", bullet, re.I)
        has_tool = re.search(r"\b(python|java|angular|react|fastapi|sql|aws|docker|api|database)\b", bullet, re.I)
        strong += int(bool(has_action)) + int(bool(has_metric)) + int(bool(has_tool))
    return min(100, int((strong / (len(bullets) * 3)) * 100))


def _clarity_score(resume: ParsedResume) -> int:
    long_lines = sum(1 for line in resume.raw_text.splitlines() if len(line) > 180)
    penalty = min(35, long_lines * 5)
    return max(45, 90 - penalty)


def _completeness_score(resume: ParsedResume) -> int:
    score = 0
    score += 20 if resume.contact.email else 0
    score += 15 if resume.contact.phone else 0
    score += 15 if resume.summary else 0
    score += 20 if resume.skills else 0
    score += 20 if resume.experience_bullets else 0
    score += 10 if resume.education else 0
    return score
