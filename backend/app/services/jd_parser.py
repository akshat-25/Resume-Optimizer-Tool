from __future__ import annotations

import logging
import re

try:
    import yake
except ImportError:
    yake = None

from app.models.schemas import ParsedJobDescription
from app.services.resume_parser import COMMON_SKILLS
from app.services.text_utils import normalize_whitespace, split_sentences, unique_preserve_order

logger = logging.getLogger(__name__)

NOISY_KEYWORDS = {
    "engineer", "developer", "manager", "role", "job", "candidate", "team",
    "required", "requirements", "responsibilities", "qualification", "qualifications",
    "backend engineer", "frontend engineer", "software engineer",
    "developer required", "required skills", "skills rest",
}


def parse_job_description(text: str) -> ParsedJobDescription:
    logger.info("Parsing job description.")
    clean_text = normalize_whitespace(text)
    lower = clean_text.lower()
    skills = [skill for skill in COMMON_SKILLS if re.search(rf"\b{re.escape(skill)}\b", lower)]
    keywords = _filter_keywords(_extract_keywords(clean_text), _guess_title(clean_text))
    technical_keywords = [keyword for keyword in keywords if _is_technical_keyword(keyword)]
    responsibilities = [
        sentence for sentence in split_sentences(clean_text)
        if re.search(r"\b(build|develop|design|manage|lead|implement|optimize|maintain|collaborate|own)\b", sentence, re.I)
    ][:12]

    required = unique_preserve_order(skills + technical_keywords[:12])
    preferred = [keyword for keyword in technical_keywords[12:24] if keyword not in required]

    logger.info(f"JD parsing complete. Found {len(required)} required skills, {len(responsibilities)} responsibilities.")

    return ParsedJobDescription(
        raw_text=clean_text,
        title=_guess_title(clean_text),
        required_skills=required[:20],
        preferred_skills=preferred[:12],
        responsibilities=responsibilities,
        keywords=unique_preserve_order(technical_keywords + skills)[:30],
    )


def _extract_keywords(text: str) -> list[str]:
    if yake is None:
        logger.warning("YAKE not found. Using fallback keyword extraction.")
        words = re.findall(r"\b[a-zA-Z][a-zA-Z+#./-]{2,}\b", text.lower())
        ignored = {"and", "the", "with", "for", "you", "our", "will", "are", "need", "role", "job"}
        counts: dict[str, int] = {}
        for word in words:
            if word not in ignored:
                counts[word] = counts.get(word, 0) + 1
        return [word for word, _ in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:30]]

    logger.debug("Extracting keywords with YAKE.")
    extractor = yake.KeywordExtractor(lan="en", n=2, dedupLim=0.9, top=30)
    return unique_preserve_order([keyword for keyword, score in extractor.extract_keywords(text) if score < 0.2])



def _filter_keywords(keywords: list[str], title: str | None) -> list[str]:
    title_parts = set(title.lower().split()) if title else set()
    filtered: list[str] = []
    for keyword in keywords:
        key = keyword.lower().strip()
        if key in NOISY_KEYWORDS:
            continue
        if any(noisy in key for noisy in {"required", "responsibilities", "qualification"}):
            continue
        if key == (title or "").lower():
            continue
        if len(key.split()) == 1 and key in title_parts and key not in COMMON_SKILLS:
            continue
        filtered.append(keyword)
    return unique_preserve_order(filtered)


def _is_technical_keyword(keyword: str) -> bool:
    key = keyword.lower().strip()
    if key in COMMON_SKILLS:
        return True
    if len(key.split()) > 1:
        return False
    if len(key.split()) > 3:
        return False
    if any(char in keyword for char in {"/", ".", "+", "#"}):
        return True
    if re.search(r"\b(api|sql|aws|ci|cd|cloud|docker|linux|python|java|rest|testing|database)\b", key):
        return True
    return False


def _guess_title(text: str) -> str | None:
    first_line = text.splitlines()[0] if text.splitlines() else ""
    if 3 <= len(first_line) <= 80 and not first_line.endswith("."):
        return first_line
    match = re.search(r"(?:job title|role)\s*[:\-]\s*(.+)", text, re.I)
    return match.group(1).strip() if match else None
