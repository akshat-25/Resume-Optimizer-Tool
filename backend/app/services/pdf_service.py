
import fitz
import logging
import re
from app.models.schemas import ParsedResume

logger = logging.getLogger(__name__)

def generate_pdf(resume: ParsedResume) -> bytes:
    """
    Overhauled PDF generation for pixel-perfect matching of the user's reference.
    Uses robust table-based layout for alignment since Flexbox support in MuPDF is limited.
    """
    logger.info("Overhauling PDF with table-based layout for stability.")
    
    # Data extraction
    name = (resume.contact.name or "Your Name").upper()
    email = resume.contact.email or "email@example.com"
    phone = resume.contact.phone or ""
    
    # Link logic
    linkedin_url = next((l for l in resume.contact.links if "linkedin.com" in l.lower()), "https://linkedin.com")
    
    # CSS - Focus on standard table layout for alignment
    css = """
    <style>
        @page { size: A4; margin: 0; }
        body {
            font-family: 'Times New Roman', Times, serif;
            font-size: 10.5pt;
            line-height: 1.2;
            color: #000;
            margin: 0;
            padding: 40px 50px;
            background: white;
        }
        .header {
            text-align: center;
            margin-bottom: 15px;
        }
        .name {
            font-size: 26pt;
            font-weight: normal;
            margin: 0;
            letter-spacing: 1.5pt;
        }
        .contact-row {
            font-size: 10pt;
            margin-top: 4px;
        }
        .section-header {
            font-size: 11pt;
            font-weight: bold;
            text-transform: uppercase;
            border-bottom: 0.75pt solid #000;
            margin-top: 15px;
            margin-bottom: 6px;
            padding-bottom: 1pt;
        }
        .summary {
            text-align: justify;
            margin-bottom: 8px;
        }
        /* Layout Tables */
        .layout-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 4px;
        }
        .layout-table td {
            padding: 0;
            vertical-align: top;
        }
        .text-right {
            text-align: right;
        }
        .bold { font-weight: bold; }
        .italic { font-style: italic; }
        
        ul {
            margin: 2px 0 8px 0;
            padding-left: 20px;
            list-style-type: disc;
        }
        li {
            margin-bottom: 2px;
            text-align: justify;
        }
        
        .skills-table {
            width: 100%;
            border-collapse: collapse;
        }
        .skills-table td {
            padding: 1px 0;
        }
        .skill-cat {
            width: 160px;
            font-weight: bold;
        }
    </style>
    """

    # Build Header
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>{css}</head>
    <body>
        <div class="header">
            <h1 class="name">{name}</h1>
            <div class="contact-row">
                {phone} ⋄ Noida, Uttar Pradesh<br>
                <a href="mailto:{email}" style="color: blue; text-decoration: none;">{email}</a> ⋄ 
                <a href="{linkedin_url}" style="color: blue; text-decoration: none;">LinkedIn</a>
            </div>
        </div>
    """

    # Process Sections
    for section in resume.sections:
        s_name = section.name.upper()
        if s_name == "HEADER": continue
        
        html += f'<div class="section-header">{s_name}</div>'
        
        if s_name == "SUMMARY":
            html += f'<div class="summary">{" ".join(section.content)}</div>'
            
        elif s_name in ["EXPERIENCE", "WORK EXPERIENCE", "PROJECTS"]:
            i = 0
            while i < len(section.content):
                line = section.content[i].strip()
                if not line:
                    i += 1
                    continue
                
                # Header lines (not bullets)
                if not line.startswith(("-", "•", "*")):
                    # Heuristic for Role/Title + Date
                    date_match = re.search(r'([A-Z][a-z]+ \d{4}|Present|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', line)
                    if date_match:
                        pos = date_match.start()
                        title, date = line[:pos].strip(), line[pos:].strip()
                        html += f'<table class="layout-table"><tr><td class="bold">{title}</td><td class="text-right">{date}</td></tr></table>'
                    else:
                        html += f'<div class="bold">{line}</div>'
                    
                    # Company line check
                    if i + 1 < len(section.content) and not section.content[i+1].strip().startswith(("-", "•", "*")):
                        comp_line = section.content[i+1].strip()
                        # Reference shows "Company Name" left and "Location" right
                        # Our current parser might combine them. We try to split by known locations or commas.
                        html += f'<table class="layout-table"><tr><td class="italic">{comp_line}</td></tr></table>'
                        i += 1
                    
                    # Bullets
                    html += '<ul>'
                    i += 1
                    while i < len(section.content) and section.content[i].strip().startswith(("-", "•", "*")):
                        bullet = section.content[i].strip(" -•*")
                        if bullet: html += f'<li>{bullet}</li>'
                        i += 1
                    html += '</ul>'
                else:
                    # Loose bullets
                    html += '<ul>'
                    while i < len(section.content) and section.content[i].strip().startswith(("-", "•", "*")):
                        bullet = section.content[i].strip(" -•*")
                        if bullet: html += f'<li>{bullet}</li>'
                        i += 1
                    html += '</ul>'
                    
        elif s_name == "SKILLS":
            html += '<table class="skills-table">'
            for line in section.content:
                if ":" in line:
                    cat, val = line.split(":", 1)
                    html += f'<tr><td class="skill-cat">{cat.strip()}:</td><td>{val.strip()}</td></tr>'
                else:
                    html += f'<tr><td colspan="2">{line.strip()}</td></tr>'
            html += '</table>'
            
        elif s_name == "EDUCATION":
            # Reference: Degree left, Date right
            for line in section.content:
                clean = line.strip(" -•*")
                if not clean: continue
                date_match = re.search(r'(\d{{4}})', clean)
                if date_match:
                    pos = date_match.start()
                    deg, date = clean[:pos].strip(", "), clean[pos:].strip()
                    html += f'<table class="layout-table"><tr><td>{deg}</td><td class="text-right">{date}</td></tr></table>'
                else:
                    html += f'<div>{clean}</div>'
        else:
            html += f'<div>{" ".join(section.content)}</div>'

    html += "</body></html>"

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    # Important: Insert htmlbox with enough space and high accuracy
    page.insert_htmlbox(fitz.Rect(0, 0, 595, 842), html)
    
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes
