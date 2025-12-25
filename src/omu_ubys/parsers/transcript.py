"""
Transcript Parser

Extracts transcript information from UBYS pages.
"""

import base64
import json
import re
from typing import List
from bs4 import BeautifulSoup

from ..models import Course, Semester
from ..exceptions import ParseError


def parse_transcript(html: str) -> List[Semester]:
    """
    Parse transcript from the transcript page.
    
    The UBYS transcript page stores data in a Base64-encoded JavaScript variable
    called _jsm, not in HTML tables.
    
    Args:
        html: HTML content of transcript page (/AIS/Student/Transcript/Index)
        
    Returns:
        list[Semester]: List of semesters with courses and grades
        
    Raises:
        ParseError: If parsing fails
        
    Example:
        >>> transcript = parse_transcript(html)
        >>> for sem in transcript:
        ...     print(f"{sem.name}: GPA {sem.gpa}")
    """
    if "Account/Login" in html:
        raise ParseError("Session expired. Please login again.")
    
    semesters = []
    
    # Try to extract _jsm variable with Base64 data
    # Pattern: _jsm = JSON.parse(Base64.decode("..."));
    pattern = r'_jsm\s*=\s*JSON\.parse\(Base64\.decode\(["\']([^"\']+)["\']\)\)'
    match = re.search(pattern, html)
    
    if match:
        try:
            base64_data = match.group(1)
            json_str = base64.b64decode(base64_data).decode('utf-8')
            data = json.loads(json_str)
            
            # Parse the transcript data
            transcripts = data.get("Transcripts", [])
            if transcripts:
                transcript = transcripts[0]
                semester_list = transcript.get("Semesters", [])
                
                for sem_data in semester_list:
                    semester_name = sem_data.get("SemesterName", "")
                    gpa = sem_data.get("SemesterAverage")
                    
                    courses = []
                    course_list = sem_data.get("Courses", [])
                    
                    for course_data in course_list:
                        code = course_data.get("CourseCode", "")
                        name = course_data.get("CourseName", "")
                        credit = course_data.get("Credit")
                        letter_grade = course_data.get("Grade", "")  # Field is "Grade", not "LetterGrade"
                        
                        if code or name:
                            courses.append(Course(
                                code=code,
                                name=name,
                                credit=credit,
                                letter_grade=letter_grade,
                            ))
                    
                    if semester_name:
                        semesters.append(Semester(
                            name=semester_name,
                            gpa=gpa,
                            courses=tuple(courses)
                        ))
            
            return semesters
        except Exception:
            pass  # Fall through to HTML parsing
    
    # Fallback: Try HTML table parsing (id="test")
    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table", id="test")
    
    if not tables:
        tables = soup.find_all("table")
        tables = [t for t in tables if t.find("caption")]
    
    for table in tables:
        caption = table.find("caption")
        if not caption:
            continue
        
        semester_name = ""
        bold = caption.find("b")
        if bold:
            semester_name = bold.get_text(strip=True)
        else:
            semester_name = caption.get_text(strip=True)
        
        courses = []
        gpa = None
        
        tbody = table.find("tbody")
        if not tbody:
            tbody = table
        
        for row in tbody.find_all("tr"):
            cells = row.find_all("td")
            
            if len(cells) < 3:
                continue
            
            row_text = row.get_text(strip=True).lower()
            if "ortalama" in row_text or "gpa" in row_text:
                for cell in cells:
                    text = cell.get_text(strip=True)
                    try:
                        gpa = float(text.replace(",", "."))
                        if 0 <= gpa <= 4:
                            break
                    except ValueError:
                        continue
                continue
            
            code = cells[0].get_text(strip=True) if len(cells) > 0 else ""
            name = cells[1].get_text(strip=True) if len(cells) > 1 else ""
            
            credit = None
            if len(cells) > 2:
                try:
                    credit = float(cells[2].get_text(strip=True).replace(",", "."))
                except ValueError:
                    pass
            
            letter_grade = cells[3].get_text(strip=True) if len(cells) > 3 else None
            
            if code or name:
                courses.append(Course(
                    code=code,
                    name=name,
                    credit=credit,
                    letter_grade=letter_grade,
                ))
        
        if semester_name:
            semesters.append(Semester(
                name=semester_name,
                gpa=gpa,
                courses=tuple(courses)
            ))
    
    return semesters

