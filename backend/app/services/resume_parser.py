from __future__ import annotations

import logging
import re

from app.models.schemas import ParsedResume, ResumeContact, ResumeSection
from app.services.bullet_quality import is_rewrite_candidate
from app.services.text_utils import normalize_whitespace, unique_preserve_order

logger = logging.getLogger(__name__)

SECTION_ALIASES = {
    "summary": {"summary", "professional summary", "profile", "objective"},
    "skills": {"skills", "technical skills", "core skills", "technologies"},
    "experience": {"experience", "work experience", "professional experience", "employment"},
    "projects": {"projects", "personal projects"},
    "education": {"education", "academic background"},
    "certifications": {"certifications", "certificates"},
}

COMMON_SKILLS = {
    "python", "fastapi", "django", "flask", "java", "javascript", "typescript",
    "angular", "react", "node.js", "node", "sql", "postgresql", "mysql", "mongodb",
    "docker", "kubernetes", "aws", "azure", "gcp", "linux", "git", "ci/cd",
    "rest", "graphql", "redis", "pandas", "numpy", "machine learning", "nlp",
    "tensorflow", "pytorch", "html", "css", "tailwind", "spring boot",
    "jenkins", "pytest", "postman", "swagger", "dynamodb", "graylog",
    "full stack", "unit testing", "microservices",
}


def parse_resume(text: str) -> ParsedResume:
    logger.info("Parsing resume text.")
    clean_text = normalize_whitespace(text)
    lines = clean_text.splitlines()
    sections = _detect_sections(lines)
    section_map = {section.name.lower(): section.content for section in sections}

    logger.debug(f"Detected sections: {[s.name for s in sections]}")

    contact = ResumeContact(
        name=_guess_name(lines),
        email=_first_match(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", clean_text),
        phone=_first_match(r"(?:\+?\d[\d\s().-]{8,}\d)", clean_text),
        links=unique_preserve_order(re.findall(r"https?://\S+|(?:linkedin|github)\.com/\S+", clean_text, re.I)),
    )
    logger.debug(f"Extracted contact info: {contact}")

    skills = _extract_skills(clean_text, section_map.get("skills", []))
    experience_bullets = _extract_bullets(section_map.get("experience", []) + section_map.get("projects", []))
    education = section_map.get("education", [])
    summary = " ".join(section_map.get("summary", [])[:4]) or None

    logger.info(f"Parsing complete. Found {len(skills)} skills and {len(experience_bullets)} bullets.")

    return ParsedResume(
        raw_text=clean_text,
        contact=contact,
        summary=summary,
        skills=skills,
        experience_bullets=experience_bullets,
        education=education,
        sections=sections,
    )



def _detect_sections(lines: list[str]) -> list[ResumeSection]:
    sections: list[ResumeSection] = []
    current_name = "Header"
    current_content: list[str] = []

    for line in lines:
        canonical = _canonical_section(line)
        if canonical:
            if current_content:
                sections.append(ResumeSection(name=current_name, content=current_content))
            current_name = canonical.title()
            current_content = []
        else:
            current_content.append(line)

    if current_content:
        sections.append(ResumeSection(name=current_name, content=current_content))

    return sections


def _canonical_section(line: str) -> str | None:
    value = re.sub(r"[^a-zA-Z /]", "", line).strip().lower()
    if len(value.split()) > 4:
        return None
    for canonical, aliases in SECTION_ALIASES.items():
        if value in aliases:
            return canonical
    return None


def _guess_name(lines: list[str]) -> str | None:
    for line in lines[:4]:
        if "@" not in line and not re.search(r"\d", line) and 2 <= len(line.split()) <= 4:
            return line
    return None


def _first_match(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text)
    return match.group(0).strip() if match else None


def _extract_skills(text: str, skill_lines: list[str]) -> list[str]:
    source = "\n".join(skill_lines) if skill_lines else text
    found = [skill for skill in COMMON_SKILLS if re.search(rf"\b{re.escape(skill)}\b", source, re.I)]
    comma_split = re.split(r"[,|•]", source)
    candidates = [item.strip(" -") for item in comma_split if 2 <= len(item.strip()) <= 32]
    return unique_preserve_order(found + candidates)[:40]


def _extract_bullets(lines: list[str]) -> list[str]:
    bullets: list[str] = []
    for line in lines:
        cleaned = line.strip(" -•\t")
        if is_rewrite_candidate(cleaned):
            bullets.append(cleaned)
    return unique_preserve_order(bullets)[:30]
