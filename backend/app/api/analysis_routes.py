import logging

logger = logging.getLogger(__name__)


from fastapi import APIRouter, File, UploadFile

from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.ats_checker import check_ats
from app.services.feedback_engine import build_resume_findings, build_rule_based_suggestions
from app.services.file_parser import extract_text_from_upload
from app.services.jd_parser import parse_job_description
from app.services.matcher import estimate_semantic_match, match_keywords
from app.services.resume_parser import parse_resume
from app.services.rewrite_service import generate_llm_suggestions
from app.services.scoring_service import score_resume

router = APIRouter(tags=["analysis"])


@router.post("/resume/extract-text")
async def extract_resume_text(file: UploadFile = File(...)) -> dict[str, str]:
    logger.info(f"Extracting text from uploaded file: {file.filename}")
    extracted_text = await extract_text_from_upload(file)
    logger.info("Successfully extracted text from file.")
    return {"text": extracted_text}


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    logger.info("Starting resume analysis.")
    resume = parse_resume(payload.resume_text)
    logger.debug("Resume parsed.")
    jd = parse_job_description(payload.job_description)
    logger.debug("Job description parsed.")
    matched, missing = match_keywords(resume, jd)
    logger.debug(f"Keywords matched: {len(matched)}, missing: {len(missing)}.")
    semantic = estimate_semantic_match(resume, jd)
    logger.debug(f"Semantic match estimated: {semantic}.")
    ats_score, ats_findings = check_ats(resume)
    logger.debug(f"ATS score: {ats_score}.")
    scores = score_resume(resume, jd, matched, semantic, ats_score)
    logger.debug("Resume scored.")
    resume_findings = build_resume_findings(resume, missing)
    rule_suggestions = build_rule_based_suggestions(resume)
    logger.debug("Findings and rule-based suggestions generated.")

    llm_available = False
    llm_suggestions = []
    if payload.use_llm:
        logger.info(f"Generating LLM suggestions with model: {payload.model}")
        llm_available, llm_suggestions = await generate_llm_suggestions(resume, jd, payload.model)
        logger.info(f"LLM suggestions generated. LLM available: {llm_available}.")

    suggestions = llm_suggestions or rule_suggestions
    logger.info("Resume analysis complete.")

    return AnalyzeResponse(
        resume=resume,
        job_description=jd,
        scores=scores,
        matched_keywords=matched,
        missing_keywords=missing,
        ats_findings=ats_findings,
        resume_findings=resume_findings,
        suggestions=suggestions,
        llm_available=llm_available,
    )
