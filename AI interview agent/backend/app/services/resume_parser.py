import os
import re
import uuid
from typing import List, Optional
from datetime import datetime
from io import BytesIO

import pypdf
from docx import Document

from app.models.resume_parsed import (
    CandidateSkill,
    CandidateEducation,
    CandidateExperience,
    CandidateProject,
    CandidateCertification,
    CandidateAchievement,
)
from sqlalchemy.orm import Session

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


def extract_pdf_text(content: bytes) -> str:
    """
    Extracts raw text from a PDF file using pypdf.
    """
    text = ""
    try:
        reader = pypdf.PdfReader(BytesIO(content))
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    return text.strip()


def extract_docx_text(content: bytes) -> str:
    """
    Extracts raw text from a DOCX file using python-docx.
    """
    text = ""
    try:
        doc = Document(BytesIO(content))
        for para in doc.paragraphs:
            if para.text:
                text += para.text + "\n"
    except Exception as e:
        raise ValueError(f"Failed to extract text from DOCX: {str(e)}")
    return text.strip()


def clean_text(text: str) -> str:
    """
    Cleans extracted text by removing excessive whitespace.
    """
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\r', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def extract_email(text: str) -> Optional[str]:
    """
    Extracts email address from text using regex.
    """
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    matches = re.findall(pattern, text)
    if matches:
        return matches[0]
    return None


def extract_phone(text: str) -> Optional[str]:
    """
    Extracts phone number from text using regex patterns.
    """
    patterns = [
        r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        r'\+?\d{10,15}',
        r'\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            phone = matches[0]
            phone = re.sub(r'[^\d+]', '', phone)
            return phone
    return None


def extract_name(text: str) -> Optional[str]:
    """
    Extracts name from the first few lines of the resume text.
    """
    lines = text.split('\n')
    for line in lines[:5]:
        line = line.strip()
        if not line:
            continue
        words = line.split()
        if 2 <= len(words) <= 4:
            if all(w[0].isupper() for w in words if w):
                return line
    return None


SECTION_HEADERS = [
    'education', 'academic qualification', 'qualification',
    'experience', 'work experience', 'professional experience', 'employment history', 'internship',
    'projects', 'personal projects', 'academic projects',
    'certifications', 'certificates', 'certification',
    'achievements', 'awards', 'honors', 'accomplishments',
    'skills', 'technical skills',
    'summary', 'objective', 'profile',
]


def _get_section_lines(text: str, target_headers: list) -> List[str]:
    """
    Generic helper to extract lines belonging to a specific section.
    Returns lines between the target header and the next section header.
    """
    lines = text.split('\n')
    captured = []
    in_section = False
    for line in lines:
        stripped = line.strip()
        lower_stripped = stripped.lower()
        if not in_section:
            for header in target_headers:
                if lower_stripped == header or lower_stripped.startswith(header + ':') or lower_stripped.startswith(header + ' '):
                    in_section = True
                    break
            continue
        header_found = False
        for header in SECTION_HEADERS:
            if lower_stripped == header or lower_stripped.startswith(header + ':') or lower_stripped.startswith(header + ' '):
                header_found = True
                break
        if header_found:
            break
        captured.append(stripped)
    return captured


def extract_skills(text: str) -> List[str]:
    """
    Extracts skills by matching against a configurable skill list.
    """
    skill_list = [
        'Python', 'Java', 'JavaScript', 'TypeScript', 'C', 'C++',
        'HTML', 'CSS', 'React', 'Node.js', 'Django', 'Flask', 'FastAPI',
        'Streamlit', 'SQL', 'MySQL', 'PostgreSQL', 'MongoDB',
        'Machine Learning', 'Deep Learning', 'Artificial Intelligence',
        'Generative AI', 'LLM', 'RAG', 'NLP', 'TensorFlow', 'PyTorch',
        'Scikit-learn', 'Pandas', 'NumPy', 'OpenCV', 'Git', 'GitHub',
        'Docker', 'AWS', 'Azure', 'GCP', 'Linux', 'Agile', 'Scrum',
    ]
    found_skills = []
    text_lower = text.lower()
    for skill in skill_list:
        pattern = r'(?<!\w)' + re.escape(skill.lower()) + r'(?!\w)'
        if re.search(pattern, text_lower):
            found_skills.append(skill)
    return found_skills


def extract_education(text: str) -> List[dict]:
    """
    Extracts education information using regex patterns.
    """
    education = []
    lines = _get_section_lines(text, ['education', 'academic qualification', 'qualification'])

    current_entry = None
    for line in lines:
        if not line:
            continue
        degree_match = re.search(
            r'(B\.?Tech|B\.?E\.?|M\.?Tech|M\.?E\.?|B\.?Sc|M\.?Sc|MBA|Ph\.?D|B\.?Com|M\.?Com|BBA|MCA|BCA|'
            r'Bachelor|Master|Doctor|Associate)\s+(of\s+)?(Science|Arts|Engineering|Commerce|Business|Computer|Technology|Artificial Intelligence|Data Science|Information Technology)?',
            line, re.IGNORECASE
        )
        if degree_match or re.search(r'(?:19|20)\d{2}', line):
            if current_entry:
                education.append(current_entry)
            current_entry = {
                'degree': line,
                'institution': None,
                'start_year': None,
                'end_year': None,
                'description': None,
            }
            years = re.findall(r'(?:19|20)\d{2}', line)
            if len(years) >= 2:
                current_entry['start_year'] = years[0]
                current_entry['end_year'] = years[1]
            elif len(years) == 1:
                current_entry['end_year'] = years[0]
            inst_match = re.search(r',\s*([^,]+?)\s*,\s*(?:19|20)\d{2}', line)
            if inst_match:
                current_entry['institution'] = inst_match.group(1).strip()
        elif current_entry and not current_entry.get('institution'):
            if len(line) < 120 and not line.startswith(('-', '•', '*')):
                current_entry['institution'] = line
        elif current_entry:
            current_entry['description'] = (current_entry.get('description') or '') + line + ' '

    if current_entry:
        education.append(current_entry)

    return education[:10]


def extract_experience(text: str) -> List[dict]:
    """
    Extracts work experience information using regex patterns.
    """
    experience = []
    lines = _get_section_lines(text, ['experience', 'work experience', 'professional experience', 'employment history', 'internship'])

    current_entry = None
    for line in lines:
        if not line:
            continue
        company_match = re.match(r'^(.+?)\s*[-–—|]\s*(.+?)\s*[-–—|]\s*(.+)$', line)
        if company_match:
            if current_entry:
                experience.append(current_entry)
            current_entry = {
                'company': company_match.group(2).strip(),
                'role': company_match.group(1).strip(),
                'start_date': None,
                'end_date': None,
                'description': '',
            }
            date_text = company_match.group(3).strip()
            date_match = re.search(r'(\w+ \d{4})\s*[-–—to]+\s*(\w+ \d{4}|Present|Current)', date_text, re.IGNORECASE)
            if date_match:
                current_entry['start_date'] = date_match.group(1)
                current_entry['end_date'] = date_match.group(2)
                current_entry['description'] = date_text.replace(date_match.group(0), '').strip() + ' '
            else:
                years = re.findall(r'(?:19|20)\d{2}', date_text)
                if len(years) >= 2:
                    current_entry['start_date'] = years[0]
                    current_entry['end_date'] = years[1]
                elif len(years) == 1:
                    current_entry['end_date'] = years[0]
                current_entry['description'] = date_text + ' '
        elif current_entry:
            if not current_entry['role'] and not re.match(r'^[\W]+$', line):
                current_entry['role'] = line
            else:
                current_entry['description'] += line + ' '

    if current_entry:
        experience.append(current_entry)

    return experience[:10]


def extract_projects(text: str) -> List[dict]:
    """
    Extracts project information using regex patterns.
    """
    projects = []
    lines = _get_section_lines(text, ['projects', 'personal projects', 'academic projects'])

    current_entry = None
    for line in lines:
        if not line:
            continue
        lower_line = line.lower()
        if lower_line.startswith(('-', '•', '*', 'technologies:', 'tech stack:', 'role:', 'responsibility:')):
            if current_entry:
                current_entry['description'] += line + ' '
            continue
        if re.match(r'^(B\.|M\.|Bachelor|Master|Doctor)', line, re.IGNORECASE):
            continue
        if re.search(r'(?:19|20)\d{2}', line) and len(line) < 50:
            continue
        if current_entry and len(line) < 80 and not line.endswith(('.', ',', ';', ':')):
            projects.append(current_entry)
            current_entry = {'project_name': line, 'technologies': None, 'description': ''}
        elif current_entry:
            current_entry['description'] += line + ' '
        else:
            current_entry = {'project_name': line, 'technologies': None, 'description': ''}

    if current_entry:
        projects.append(current_entry)

    return projects[:10]


def extract_certifications(text: str) -> List[dict]:
    """
    Extracts certification information using regex patterns.
    """
    certifications = []
    lines = _get_section_lines(text, ['certifications', 'certificates', 'certification'])

    current_entry = None
    for line in lines:
        if not line:
            continue
        if current_entry:
            certifications.append(current_entry)
        current_entry = {
            'certification_name': line,
            'organization': None,
            'year': None,
        }
        years = re.findall(r'(?:19|20)\d{2}', line)
        if years:
            current_entry['year'] = years[-1]
        org_match = re.search(r'[-–—|]\s*([A-Za-z\s&]+?)(?:\s*[-–—|]|$)', line)
        if org_match:
            current_entry['organization'] = org_match.group(1).strip()

    if current_entry:
        certifications.append(current_entry)

    return certifications[:10]


def extract_achievements(text: str) -> List[str]:
    """
    Extracts achievements from the resume text.
    """
    achievements = []
    lines = _get_section_lines(text, ['achievements', 'awards', 'honors', 'accomplishments'])

    for line in lines:
        if not line:
            continue
        if len(line.strip()) > 5:
            achievements.append(line.strip())

    return achievements[:10]


def extract_location(text: str) -> Optional[str]:
    """
    Extracts location from resume text using common patterns.
    """
    tech_keywords = {'python', 'java', 'javascript', 'git', 'docker', 'aws', 'sql', 'react', 'node', 'django', 'flask', 'fastapi', 'pandas', 'numpy'}
    patterns = [
        r'(?:Location|Address|City|Based in|Located in)[:\s]+([A-Za-z\s,]+?)(?:\n|$)',
        r'(?<!\w)([A-Za-z][A-Za-z\s]+,\s*[A-Z]{2})(?!\w)',
        r'(?<!\w)([A-Za-z][A-Za-z\s]+,\s*[A-Za-z][A-Za-z\s]+)(?=\n|$)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            loc = match.group(1).strip()
            if 3 <= len(loc) <= 100 and '.' not in loc and '@' not in loc:
                words = set(loc.lower().replace(',', ' ').split())
                if not words & tech_keywords:
                    return loc
    return None


def extract_linkedin(text: str) -> Optional[str]:
    """
    Extracts LinkedIn URL from resume text.
    """
    patterns = [
        r'https?://(?:www\.)?linkedin\.com/in/[A-Za-z0-9\-_]+',
        r'linkedin\.com/in/[A-Za-z0-9\-_]+',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            url = match.group(0)
            if not url.startswith('http'):
                url = 'https://' + url
            return url
    return None


def extract_github(text: str) -> Optional[str]:
    """
    Extracts GitHub URL from resume text.
    """
    patterns = [
        r'https?://(?:www\.)?github\.com/[A-Za-z0-9\-_]+',
        r'github\.com/[A-Za-z0-9\-_]+',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            url = match.group(0)
            if not url.startswith('http'):
                url = 'https://' + url
            return url
    return None


def extract_portfolio(text: str) -> Optional[str]:
    """
    Extracts portfolio/personal website URL from resume text.
    """
    patterns = [
        r'https?://(?:www\.)?[A-Za-z0-9\-]+\.(?:dev|io|me|tech|app|site|xyz|co(?!m)|online|website)(?:\/[^\s]*)?',
        r'(?:Portfolio|Website|Blog)[:\s]+(https?://[^\s]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if match.lastindex is None:
                url = match.group(0)
            else:
                url = match.group(1)
            return url.strip()
    return None


def parse_resume(file_content: bytes, file_extension: str) -> dict:
    """
    Main resume parsing function.
    """
    if file_extension.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file extension: {file_extension}")

    if len(file_content) > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File exceeds maximum size of 5 MB")

    if len(file_content) == 0:
        raise ValueError("Empty file provided")

    if file_extension.lower() == '.pdf':
        raw_text = extract_pdf_text(file_content)
    else:
        raw_text = extract_docx_text(file_content)

    if not raw_text or len(raw_text.strip()) < 10:
        raise ValueError("No extractable text found in resume")

    cleaned_text = clean_text(raw_text)

    return {
        'raw_text': cleaned_text,
        'name': extract_name(cleaned_text),
        'email': extract_email(cleaned_text),
        'phone': extract_phone(cleaned_text),
        'location': extract_location(cleaned_text),
        'linkedin_url': extract_linkedin(cleaned_text),
        'github_url': extract_github(cleaned_text),
        'portfolio_url': extract_portfolio(cleaned_text),
        'skills': extract_skills(cleaned_text),
        'education': extract_education(cleaned_text),
        'experience': extract_experience(cleaned_text),
        'projects': extract_projects(cleaned_text),
        'certifications': extract_certifications(cleaned_text),
        'achievements': extract_achievements(cleaned_text),
    }


def save_parsed_data(db: Session, student_id: int, parsed_data: dict) -> None:
    """
    Saves parsed resume data to MySQL, replacing existing data for the student.
    """
    db.query(CandidateSkill).filter(CandidateSkill.student_id == student_id).delete()
    db.query(CandidateEducation).filter(CandidateEducation.student_id == student_id).delete()
    db.query(CandidateExperience).filter(CandidateExperience.student_id == student_id).delete()
    db.query(CandidateProject).filter(CandidateProject.student_id == student_id).delete()
    db.query(CandidateCertification).filter(CandidateCertification.student_id == student_id).delete()
    db.query(CandidateAchievement).filter(CandidateAchievement.student_id == student_id).delete()

    for skill in parsed_data.get('skills', []):
        db.add(CandidateSkill(student_id=student_id, skill=skill))

    for edu in parsed_data.get('education', []):
        db.add(CandidateEducation(
            student_id=student_id,
            degree=edu.get('degree'),
            institution=edu.get('institution'),
            start_year=edu.get('start_year'),
            end_year=edu.get('end_year'),
            description=edu.get('description'),
        ))

    for exp in parsed_data.get('experience', []):
        db.add(CandidateExperience(
            student_id=student_id,
            company=exp.get('company'),
            role=exp.get('role'),
            start_date=exp.get('start_date'),
            end_date=exp.get('end_date'),
            description=exp.get('description'),
        ))

    for proj in parsed_data.get('projects', []):
        db.add(CandidateProject(
            student_id=student_id,
            project_name=proj.get('project_name'),
            technologies=proj.get('technologies'),
            description=proj.get('description'),
        ))

    for cert in parsed_data.get('certifications', []):
        db.add(CandidateCertification(
            student_id=student_id,
            certification_name=cert.get('certification_name'),
            organization=cert.get('organization'),
            year=cert.get('year'),
        ))

    for achievement in parsed_data.get('achievements', []):
        db.add(CandidateAchievement(
            student_id=student_id,
            achievement=achievement,
        ))

    db.commit()


def get_parsed_data(db: Session, student_id: int) -> dict:
    """
    Retrieves all parsed resume data for a student from MySQL.
    """
    skills = db.query(CandidateSkill).filter(CandidateSkill.student_id == student_id).all()
    education = db.query(CandidateEducation).filter(CandidateEducation.student_id == student_id).all()
    experience = db.query(CandidateExperience).filter(CandidateExperience.student_id == student_id).all()
    projects = db.query(CandidateProject).filter(CandidateProject.student_id == student_id).all()
    certifications = db.query(CandidateCertification).filter(CandidateCertification.student_id == student_id).all()
    achievements = db.query(CandidateAchievement).filter(CandidateAchievement.student_id == student_id).all()

    return {
        'skills': [s.skill for s in skills],
        'education': [{'degree': e.degree, 'institution': e.institution, 'start_year': e.start_year, 'end_year': e.end_year, 'description': e.description} for e in education],
        'experience': [{'company': e.company, 'role': e.role, 'start_date': e.start_date, 'end_date': e.end_date, 'description': e.description} for e in experience],
        'projects': [{'project_name': p.project_name, 'technologies': p.technologies, 'description': p.description} for p in projects],
        'certifications': [{'certification_name': c.certification_name, 'organization': c.organization, 'year': c.year} for c in certifications],
        'achievements': [a.achievement for a in achievements],
    }
