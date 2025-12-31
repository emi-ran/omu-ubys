"""
Grades Parser

Extracts grade information from UBYS pages.
"""

import re
from typing import List, Optional
from urllib.parse import unquote

from bs4 import BeautifulSoup

from ..models import Course, Exam, Semester, ClassDetail, Student, Instructor
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


def parse_class_detail(html: str) -> ClassDetail:
    """
    Parse detailed class information from the class detail page.
    
    Args:
        html: HTML content of class detail page
        
    Returns:
        ClassDetail: Detailed class information including exams and instructor
    """
    soup = BeautifulSoup(html, "lxml")
    
    exams = []
    instructor = None
    class_average = None
    letter_grade = None
    
    # 1. Parse Letter Grade (Success Status)
    # The success-status div contains something like "Durumu Netleşmemiş" or "Başarılı (AA)"
    status_elem = soup.find("div", class_="success-status")
    if status_elem:
        status_text = status_elem.get_text(strip=True)
        # Try to extract letter grade like AA, BA, BB, etc.
        match = re.search(r'\b(AA|BA|BB|CB|CC|DC|DD|FD|FF)\b', status_text)
        if match:
            letter_grade = match.group(1)
        else:
            # Keep the full status text if no letter grade found
            letter_grade = status_text if status_text and "Netleşmemiş" not in status_text else None
    
    # 2. Parse Exams from the main table
    # Find the exam table - it's inside div.table-responsive inside the active tab-pane
    # Headers: Sınav Tipi | Sınav Adı | İlan Tarihi | Sınav Notu | Mazeret | Sınıf Sıralaması | Sınıf Ortalaması
    tab_pane = soup.find("div", class_="tab-pane active")
    if not tab_pane:
        tab_pane = soup
    
    table_container = tab_pane.select_one('.table-responsive table')
    if not table_container:
        # Fallback: find any table with exam headers
        for table in soup.find_all("table"):
            thead = table.find("thead")
            if thead and ("Sınav Tipi" in thead.get_text() or "Sınav Notu" in thead.get_text()):
                table_container = table
                break
    
    if table_container:
        tbody = table_container.find("tbody")
        if tbody:
            for row in tbody.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) >= 4:
                    exam_type = cells[0].get_text(strip=True)
                    exam_name = cells[1].get_text(strip=True)
                    date = cells[2].get_text(strip=True)
                    
                    # Parse score (column index 3)
                    score_text = cells[3].get_text(strip=True)
                    score = None
                    if score_text and score_text != "-":
                        try:
                            score = float(score_text.replace(",", "."))
                        except ValueError:
                            pass
                    
                    ranking = None
                    average = None
                    
                    # Column 4 is Mazeret (excuse), skip it
                    # Column 5 is Sınıf Sıralaması (class rank)
                    # Column 6 is Sınıf Ortalaması (class average)
                    if len(cells) >= 6:
                        ranking_text = cells[5].get_text(strip=True)
                        if ranking_text and ranking_text != "-":
                            ranking = ranking_text
                    
                    if len(cells) >= 7:
                        avg_text = cells[6].get_text(strip=True)
                        if avg_text and avg_text != "-":
                            try:
                                average = float(avg_text.replace(",", "."))
                            except ValueError:
                                pass
                    
                    exams.append(Exam(
                        exam_type=exam_type,
                        name=exam_name,
                        date=date,
                        score=score,
                        ranking=ranking,
                        average=average
                    ))

    # 3. Parse Instructor
    instructor_div = soup.find("div", class_="instructor")
    if instructor_div:
        # Image
        img_tag = instructor_div.find("img")
        img_url = img_tag.get("src") if img_tag else None
        
        # Name - inside div.name > a
        name_div = instructor_div.find("div", class_="name")
        if name_div:
            name_link = name_div.find("a")
            name = name_link.get_text(strip=True) if name_link else name_div.get_text(strip=True)
        else:
            name = None
        
        if name:
            instructor = Instructor(name=name, image_url=img_url)
        
        # 4. Parse Class Average (inside instructor div .avarage class)
        avg_div = instructor_div.find("div", class_="avarage")
        if avg_div:
            # Look for patterns like "Not Ortalaması : 30,8"
            text = avg_div.get_text()
            # Try to find any number after Ortalaması
            match = re.search(r'Ortalaması\s*:\s*([\d,]+(?:\.\d+)?)', text)
            if match:
                class_average = match.group(1)

    return ClassDetail(
        exams=tuple(exams),
        instructor=instructor,
        class_average=class_average,
        letter_grade=letter_grade
    )



def parse_student_list(html: str) -> List[Student]:
    """
    Parse the list of students from the student list page/fragment.
    
    Args:
        html: HTML content of the student list
        
    Returns:
        List[Student]: List of students
    """
    soup = BeautifulSoup(html, "lxml")
    students = []
    
    # Table with class="table table-condensed table-hover"
    # Usually has "Dersi Alan Diğer Öğrenciler" heading
    
    # Try finding the specific student tableRows
    rows = soup.select("table.table-hover tbody tr")
    
    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 3:
            # cell 0: Image
            img_tag = cells[0].find("img")
            student_id = ""
            image_url = None
            
            if img_tag:
                 image_url = img_tag.get("src")
                 student_id = img_tag.get("data-user-id", "")
            
            name = cells[1].get_text(strip=True)
            surname = cells[2].get_text(strip=True)
            
            if student_id: # Only add if we found a valid row with ID
                students.append(Student(
                    id=student_id,
                    name=name,
                    surname=surname,
                    image_url=image_url
                ))
                
    return students
