import logging
from fastapi import APIRouter, File, UploadFile, Response, HTTPException
from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.ats_checker import check_ats
from app.services.feedback_engine import build_resume_findings, build_rule_based_suggestions
from app.services.file_parser import extract_text_from_upload
from app.services.jd_parser import parse_job_description
from app.services.matcher import estimate_semantic_match, match_keywords
from app.services.resume_parser import parse_resume
from app.services.rewrite_service import generate_llm_suggestions
from app.services.scoring_service import score_resume
from app.services.reconstruction_service import apply_suggestions
from app.services.pdf_service import generate_pdf

logger = logging.getLogger(__name__)

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
    jd = parse_job_description(payload.job_description)
    matched, missing = match_keywords(resume, jd)
    semantic = estimate_semantic_match(resume, jd)
    ats_score, ats_findings = check_ats(resume)
    scores = score_resume(resume, jd, matched, semantic, ats_score)
    resume_findings = build_resume_findings(resume, missing)
    rule_suggestions = build_rule_based_suggestions(resume)

    llm_available = False
    llm_suggestions = []
    if payload.use_llm:
        logger.info(f"Generating LLM suggestions with model: {payload.model}")
        llm_available, llm_suggestions = await generate_llm_suggestions(resume, jd, payload.model)

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

@router.post("/resume/download-pdf")
async def reconstruct_pdf(payload: AnalyzeResponse) -> Response:
    """
    Take an analysis response and generate a modified PDF file.
    """
    try:
        logger.info("Reconstructing resume as PDF.")
        # 1. Apply suggestions to the resume data
        modified_resume = apply_suggestions(payload.resume, payload.suggestions)
        
        # 2. Generate PDF bytes
        pdf_bytes = generate_pdf(modified_resume)
        
        logger.info("PDF generation successful.")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=optimized_resume.pdf"}
        )
    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")
