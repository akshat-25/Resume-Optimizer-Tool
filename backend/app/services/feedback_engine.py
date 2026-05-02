from __future__ import annotations

import logging
from app.models.schemas import Finding, ParsedResume, Suggestion
from app.services.bullet_quality import fallback_rewrite, is_weak_bullet

logger = logging.getLogger(__name__)


def build_resume_findings(resume: ParsedResume, missing_keywords: list[str]) -> list[Finding]:
    logger.info("Building resume findings.")
    findings: list[Finding] = []
    weak_bullets = [bullet for bullet in resume.experience_bullets if is_weak_bullet(bullet)]

    if weak_bullets:
        logger.debug(f"Found {len(weak_bullets)} weak bullets.")
        findings.append(Finding(
            severity="high",
            issue=f"{len(weak_bullets)} weak experience bullets found",
            why_it_matters="Generic bullets do not show scope, tools, or outcome.",
            action="Rewrite bullets with action verb + technology + contribution + measurable result when true.",
        ))

    if missing_keywords:
        logger.debug(f"Found {len(missing_keywords)} missing keywords.")
        findings.append(Finding(
            severity="medium",
            issue="Important job keywords are missing",
            why_it_matters="Relevant keywords help ATS matching and recruiter scanning.",
            action="Add missing skills only where they reflect your real experience.",
        ))

    return findings


def build_rule_based_suggestions(resume: ParsedResume) -> list[Suggestion]:
    logger.info("Building rule-based suggestions.")
    suggestions: list[Suggestion] = []
    for bullet in resume.experience_bullets[:10]:
        if is_weak_bullet(bullet):
            suggestions.append(Suggestion(
                section="Experience",
                before=bullet,
                after=fallback_rewrite(bullet),
                why_it_is_better="Keeps the original fact pattern and prompts for a measurable outcome only if you can verify it.",
                needs_verification=True,
                questions=[
                    "Can you add a metric such as time saved, latency reduced, revenue, or user scale?",
                ],
            ))
    logger.debug(f"Generated {len(suggestions)} rule-based suggestions.")
    return suggestions[:6]

