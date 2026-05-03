
import logging
import re

from app.models.schemas import Finding, ParsedResume

logger = logging.getLogger(__name__)


def check_ats(resume: ParsedResume) -> tuple[int, list[Finding]]:
    logger.info("Running ATS check.")
    findings: list[Finding] = []
    score = 100

    if not resume.contact.email:
        score -= 12
        findings.append(_finding("high", "Missing email address", "Recruiters and ATS systems need a clear email field.", "Add a plain text email near the top."))

    if not resume.contact.phone:
        score -= 8
        findings.append(_finding("medium", "Missing phone number", "Some ATS profiles expect a phone field.", "Add a standard phone number near your name."))

    section_names = {section.name.lower() for section in resume.sections}
    for required in ["skills", "experience", "education"]:
        if required not in section_names:
            score -= 10
            findings.append(_finding("medium", f"Missing standard {required} section", "ATS parsers perform better with conventional section names.", f"Add a section named '{required.title()}'."))

    symbol_count = len(re.findall(r"[★✓◆■●]", resume.raw_text))
    if symbol_count > 4:
        score -= 8
        findings.append(_finding("low", "Decorative symbols detected", "Icons and decorative bullets can parse poorly.", "Use simple hyphen or bullet characters."))

    if "\t" in resume.raw_text:
        score -= 6
        findings.append(_finding("low", "Tab-heavy layout detected", "Tabular layouts can scramble reading order.", "Use a single-column ATS-safe layout."))

    return max(0, score), findings


def _finding(severity: str, issue: str, why: str, action: str) -> Finding:
    return Finding(severity=severity, issue=issue, why_it_matters=why, action=action)
