
from typing import List, Optional

from pydantic import BaseModel, Field


class ResumeContact(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    links: List[str] = Field(default_factory=list)


class ResumeSection(BaseModel):
    name: str
    content: List[str]


class ParsedResume(BaseModel):
    raw_text: str
    contact: ResumeContact
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience_bullets: List[str] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    sections: List[ResumeSection] = Field(default_factory=list)


class ParsedJobDescription(BaseModel):
    raw_text: str
    title: Optional[str] = None
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)


class ScoreBreakdown(BaseModel):
    overall: int
    ats: int
    keyword_match: int
    semantic_match: int
    impact: int
    clarity: int
    completeness: int


class Finding(BaseModel):
    severity: str
    issue: str
    why_it_matters: str
    action: str


class Suggestion(BaseModel):
    section: str
    before: str
    after: str
    why_it_is_better: str
    needs_verification: bool = False
    questions: List[str] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    resume_text: str
    job_description: str
    model: str = "qwen3:8b"
    use_llm: bool = True


class AnalyzeResponse(BaseModel):
    resume: ParsedResume
    job_description: ParsedJobDescription
    scores: ScoreBreakdown
    matched_keywords: List[str]
    missing_keywords: List[str]
    ats_findings: List[Finding]
    resume_findings: List[Finding]
    suggestions: List[Suggestion]
    llm_available: bool
