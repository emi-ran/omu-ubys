"""
Grades Parser

Extracts grade information from UBYS pages.
"""

import re
from typing import List, Optional
from urllib.parse import unquote

from bs4 import BeautifulSoup

from ..models import Course, Exam, Semester
from ..exceptions import ParseError


def parse_grades(html: str) -> List[Semester]:
    """
    Parse grades from the grades page.
    
    Args:
        html: HTML content of the grades page (/AIS/Student/Class/Index)
        
    Returns:
        list[Semester]: List of semesters with their courses
        
    Raises:
        ParseError: If parsing fails
        
    Example:
        >>> semesters = parse_grades(html)
        >>> for sem in semesters:
        ...     print(f"{sem.name}: {len(sem.courses)} courses")
    """
    if "Account/Login" in html:
        raise ParseError("Session expired. Please login again.")
    
    soup = BeautifulSoup(html, "lxml")
    semesters = []
    
    # Each semester is in a panel
    panels = soup.find_all("div", class_="panel-default")
    
    for panel in panels:
        # Get semester name from panel heading
        heading = panel.find("div", class_="panel-heading")
        if not heading:
            continue
        
        semester_name = heading.get_text(strip=True)
        courses = []
        
        # Find the table body
        tbody = panel.find("tbody")
        if not tbody:
            continue
        
        rows = tbody.find_all("tr")
        i = 0
        
        while i < len(rows):
            row = rows[i]
            cells = row.find_all("td")
            
            # Main course row has rowspan="2"
            if cells and cells[0].get("rowspan") == "2":
                course = _parse_course_row(cells)
                
                # Next row contains exam details
                if i + 1 < len(rows):
                    exam_row = rows[i + 1]
                    exams = _parse_exam_row(exam_row)
                    course = Course(
                        code=course.code,
                        name=course.name,
                        credit=course.credit,
                        letter_grade=course.letter_grade,
                        status=course.status,
                        class_id=course.class_id,
                        exams=tuple(exams)
                    )
                    i += 1
                
                courses.append(course)
            
            i += 1
        
        if courses:
            semesters.append(Semester(
                name=semester_name,
                courses=tuple(courses)
            ))
    
    return semesters


def _parse_course_row(cells: list) -> Course:
    """Parse a single course row."""
    code = ""
    class_id = None
    
    # Course code is in cells[0] - link is also here!
    if len(cells) > 0:
        code_cell = cells[0]
        code = code_cell.get_text(strip=True)
        
        # Extract classId from link in the code cell (not name cell!)
        link = code_cell.find("a")
        if link and link.get("href"):
            href = link.get("href")
            match = re.search(r"classId=([^&'\"]+)", href)
            if match:
                class_id = unquote(match.group(1))
    
    # Course name is in cells[1]
    name = ""
    if len(cells) > 1:
        name = cells[1].get_text(strip=True)
    
    credit = None
    if len(cells) > 2:
        try:
            credit = float(cells[2].get_text(strip=True).replace(",", "."))
        except (ValueError, AttributeError):
            pass
    
    # Column 6: Geçme Notu (passing grade, numeric)
    # Column 7: HBN = Harf Notu (letter grade like AA, BA)
    # Column 8: Başarı Durumu (status)
    letter_grade = cells[7].get_text(strip=True) if len(cells) > 7 else None
    status = cells[8].get_text(strip=True) if len(cells) > 8 else None
    
    return Course(
        code=code,
        name=name,
        credit=credit,
        letter_grade=letter_grade,
        status=status,
        class_id=class_id,
    )


def _parse_exam_row(row) -> List[Exam]:
    """Parse exam details from the row below course info."""
    exams = []
    
    # Exam details are usually in nested tables or spans
    cells = row.find_all("td")
    
    for cell in cells:
        text = cell.get_text(strip=True)
        if not text:
            continue
        
        # Try to parse exam info (format varies)
        # Common patterns: "Vize: 75", "Final: 80"
        patterns = [
            (r"Vize[:\s]*(\d+(?:[.,]\d+)?)", "Vize"),
            (r"Final[:\s]*(\d+(?:[.,]\d+)?)", "Final"),
            (r"Bütünleme[:\s]*(\d+(?:[.,]\d+)?)", "Bütünleme"),
        ]
        
        for pattern, exam_type in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    score = float(match.group(1).replace(",", "."))
                    exams.append(Exam(exam_type=exam_type, name=exam_type, score=score))
                except ValueError:
                    pass
    
    return exams


def parse_class_detail(html: str) -> dict:
    """
    Parse detailed class information.
    
    Args:
        html: HTML content of class detail page
        
    Returns:
        dict: Contains passing_grade, letter_grade, and exam_list
        
    Example:
        >>> detail = parse_class_detail(html)
        >>> print(detail["letter_grade"])
        "AA"
    """
    soup = BeautifulSoup(html, "lxml")
    
    result = {
        "passing_grade": None,
        "letter_grade": None,
        "exams": []
    }
    
    # Find success status
    status_elem = soup.find(class_="success-status")
    if status_elem:
        text = status_elem.get_text(strip=True)
        result["letter_grade"] = text
    
    # Find exam table - use .table-responsive table selector
    table_container = soup.select_one('.table-responsive table')
    if not table_container:
        table_container = soup.find("table")
    
    if table_container:
        tbody = table_container.find("tbody")
        if tbody:
            for row in tbody.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) >= 4:
                    exam = {
                        "type": cells[0].get_text(strip=True),
                        "name": cells[1].get_text(strip=True),
                        "date": cells[2].get_text(strip=True),
                        "score": cells[3].get_text(strip=True),
                    }
                    if len(cells) >= 7:
                        exam["ranking"] = cells[5].get_text(strip=True)
                        exam["average"] = cells[6].get_text(strip=True)
                    result["exams"].append(exam)
    
    return result
