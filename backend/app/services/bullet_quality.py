from __future__ import annotations

import re
from difflib import SequenceMatcher

ACTION_VERBS = {
    "achieved", "automated", "built", "collaborated", "conducted", "contributed",
    "created", "delivered", "designed", "developed", "implemented", "improved",
    "integrated", "launched", "led", "managed", "monitored", "optimized",
    "owned", "reduced", "scaled", "supported", "tested",
}

JOB_TITLE_WORDS = {
    "engineer", "developer", "manager", "analyst", "intern", "associate",
    "consultant", "lead", "architect", "specialist",
}

LOCATION_WORDS = {
    "india", "uttar", "pradesh", "noida", "delhi", "gurgaon", "gurugram",
    "bangalore", "bengaluru", "mumbai", "pune", "hyderabad", "chennai",
    "remote", "onsite", "hybrid",
}


def is_rewrite_candidate(text: str) -> bool:
    cleaned = _clean(text)
    words = cleaned.split()
    lower = cleaned.lower()

    if len(words) < 7 or len(words) > 55:
        return False
    if _is_date_line(cleaned) or _is_location_line(cleaned) or _is_title_or_company_line(cleaned):
        return False
    if cleaned.count(",") >= 5 and not _has_action_signal(lower):
        return False

    return _has_action_signal(lower) or _has_technical_contribution(lower)


def is_weak_bullet(text: str) -> bool:
    if not is_rewrite_candidate(text):
        return False

    lower = text.lower()
    has_metric = bool(re.search(r"\d+%?|\b(users|requests|latency|revenue|cost|hours|seconds|minutes)\b", lower))
    has_specific_tool = bool(re.search(r"\b(python|java|angular|react|fastapi|flask|django|sql|aws|docker|api|database|redis|mysql|jenkins|pytest|postman)\b", lower))
    too_short = len(text.split()) < 11
    has_action = _has_action_signal(lower)
    has_scope = _has_technical_contribution(lower) or len(text.split()) >= 14
    is_already_strong = has_action and has_scope and (has_metric or has_specific_tool)
    return not is_already_strong or too_short


def sanitize_rewrite(before: str, after: str, previous_after: list[str]) -> str | None:
    cleaned = _clean(after)
    if not cleaned:
        return None
    if len(cleaned.split()) > 45:
        return None
    if _looks_like_resume_metadata(cleaned):
        return None
    if _similarity(before, cleaned) > 0.96:
        return None
    if any(_similarity(existing, cleaned) > 0.82 for existing in previous_after):
        return None
    return cleaned


def fallback_rewrite(before: str) -> str:
    cleaned = _clean(before).rstrip(".")
    if re.search(r"\d|users|requests|latency|revenue|cost|hours", cleaned, re.I):
        return cleaned + "."
    return f"{cleaned}, improving [measurable outcome if true]."


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip(" -•\t")).strip()


def _is_date_line(text: str) -> bool:
    return bool(re.fullmatch(
        r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+\d{4}\s*[-–]\s*(?:present|current|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+\d{4}|\d{4})",
        text.strip(),
        re.I,
    ))


def _is_location_line(text: str) -> bool:
    words = [re.sub(r"[^a-z]", "", word.lower()) for word in text.split()]
    words = [word for word in words if word]
    if not words or len(words) > 5:
        return False
    return sum(1 for word in words if word in LOCATION_WORDS) >= max(1, len(words) - 1)


def _is_title_or_company_line(text: str) -> bool:
    words = [re.sub(r"[^a-z]", "", word.lower()) for word in text.split()]
    words = [word for word in words if word]
    if not words or len(words) > 6:
        return False
    has_title_word = any(word in JOB_TITLE_WORDS for word in words)
    looks_like_name = text[:1].isupper() and not _has_action_signal(text.lower())
    has_company_suffix = bool(re.search(r"\b(technologies|solutions|systems|labs|inc|llc|pvt|ltd)\b", text, re.I))
    return has_company_suffix or (has_title_word and looks_like_name)


def _has_action_signal(lower: str) -> bool:
    first_word = re.sub(r"[^a-z]", "", lower.split()[0]) if lower.split() else ""
    return first_word in ACTION_VERBS or any(re.search(rf"\b{verb}\b", lower) for verb in ACTION_VERBS)


def _has_technical_contribution(lower: str) -> bool:
    return bool(re.search(r"\b(api|backend|frontend|database|pipeline|service|feature|dashboard|automation|integration|testing|deployment)\b", lower))


def _looks_like_resume_metadata(text: str) -> bool:
    return _is_date_line(text) or _is_location_line(text) or _is_title_or_company_line(text)


def _similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, left.lower(), right.lower()).ratio()
