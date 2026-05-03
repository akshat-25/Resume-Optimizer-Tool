
import logging
from app.models.schemas import ParsedResume, Suggestion, ResumeSection

logger = logging.getLogger(__name__)

def apply_suggestions(resume: ParsedResume, suggestions: list[Suggestion]) -> ParsedResume:
    """
    Merge suggestions back into the resume structure.
    Currently focuses on experience bullets.
    """
    logger.info(f"Applying {len(suggestions)} suggestions to resume.")
    
    # Create a map for quick lookup
    suggestion_map = {s.before.strip().lower(): s.after for s in suggestions}
    
    new_sections = []
    for section in resume.sections:
        new_content = []
        for line in section.content:
            clean_line = line.strip(" -•\t")
            # If line matches a 'before' suggestion, use 'after'
            if clean_line.lower() in suggestion_map:
                logger.debug(f"Replacing bullet in section {section.name}")
                # Preserve some original formatting if possible (bullet points)
                prefix = ""
                if line.lstrip().startswith(("-", "•")):
                    prefix = line[:line.find(line.lstrip()[0]) + 1] + " "
                new_content.append(prefix + suggestion_map[clean_line.lower()])
            else:
                new_content.append(line)
        
        new_sections.append(ResumeSection(name=section.name, content=new_content))

    # Update the flat experience_bullets as well for consistency
    new_exp_bullets = []
    for bullet in resume.experience_bullets:
        if bullet.lower() in suggestion_map:
            new_exp_bullets.append(suggestion_map[bullet.lower()])
        else:
            new_exp_bullets.append(bullet)

    return ParsedResume(
        raw_text=resume.raw_text, # raw text remains unchanged as it's the original source
        contact=resume.contact,
        summary=resume.summary,
        skills=resume.skills,
        experience_bullets=new_exp_bullets,
        education=resume.education,
        sections=new_sections
    )
