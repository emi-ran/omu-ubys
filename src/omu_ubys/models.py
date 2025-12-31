"""
OMU-UBYS Data Models

This module contains dataclasses representing UBYS data structures.
All models are immutable (frozen) for safety.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class UserProfile:
    """
    Represents a student's profile information.
    
    Attributes:
        name: Full name of the student
        student_number: Student ID number (e.g., "221234567")
        faculty: Faculty name (e.g., "Mühendislik Fakültesi")
        department: Department name (e.g., "Bilgisayar Mühendisliği")
        sap_id: Academic program ID (used internally for API calls)
        db_student_id: Database student ID (used for schedule requests)
        semester_id: Current semester number
        year: Current academic year
    """
    name: str
    student_number: str
    faculty: str
    department: str
    sap_id: Optional[str] = None
    db_student_id: Optional[int] = None
    semester_id: Optional[int] = None
    year: Optional[int] = None
    gano: Optional[float] = None  # Cumulative GPA (Genel Akademik Not Ortalaması)


@dataclass(frozen=True)
class Advisor:
    """
    Represents academic advisor information.
    
    Attributes:
        name: Full name of the advisor
        email: Email address of the advisor
    """
    name: str
    email: Optional[str] = None


@dataclass(frozen=True)
class Exam:
    """
    Represents a single exam result.
    
    Attributes:
        exam_type: Type of exam (e.g., "Vize", "Final", "Bütünleme")
        name: Exam name/description
        date: Exam date (if available)
        score: Student's score
        average: Class average (if available)
        ranking: Student's ranking in class (if available)
    """
    exam_type: str
    name: str
    date: Optional[str] = None
    score: Optional[float] = None
    average: Optional[float] = None
    ranking: Optional[str] = None


@dataclass(frozen=True)
class Course:
    """
    Represents a single course with grade information.
    
    Attributes:
        code: Course code (e.g., "BİL101")
        name: Course name (e.g., "Programlamaya Giriş")
        credit: Credit hours
        letter_grade: Final letter grade (e.g., "AA", "BA", "BB")
        status: Pass/fail status (e.g., "Başarılı", "Başarısız")
        class_id: Internal course ID for detailed queries
        exams: List of exam results for this course
    """
    code: str
    name: str
    credit: Optional[float] = None
    letter_grade: Optional[str] = None
    status: Optional[str] = None
    class_id: Optional[str] = None
    exams: tuple[Exam, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Semester:
    """
    Represents a semester with its courses.
    
    Attributes:
        name: Semester name (e.g., "2023-2024 Güz", "1. Yarıyıl")
        gpa: Semester GPA (if available)
        courses: List of courses taken in this semester
    """
    name: str
    gpa: Optional[float] = None
    courses: tuple[Course, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ScheduleItem:
    """
    Represents a single item in the weekly schedule.
    
    Attributes:
        day: Day of the week (e.g., "Pazartesi")
        start_time: Start time (e.g., "09:00")
        end_time: End time (e.g., "09:45")
        course_name: Name of the course
        course_code: Course code (if available)
        classroom: Classroom/location
        instructor: Instructor name (if available)
    """
    day: str
    start_time: str
    end_time: str
    course_name: str
    course_code: Optional[str] = None
    classroom: Optional[str] = None
    instructor: Optional[str] = None


@dataclass(frozen=True)
class WeeklyTopic:
    """
    Represents a weekly topic from course syllabus.
    
    Attributes:
        week: Week number
        topic: Topic/content for that week
    """
    week: int
    topic: str


@dataclass(frozen=True)
class MenuItem:
    """
    Represents a single menu item from cafeteria.
    
    Attributes:
        name: Name of the dish
        category: Category type (e.g., "Çorba", "Yemek", "Yemek 2")
        calories: Calorie information (if available)
    """
    name: str
    category: Optional[str] = None
    calories: Optional[int] = None


@dataclass(frozen=True)
class CafeteriaMenu:
    """
    Represents the daily cafeteria menu.
    
    Attributes:
        date: Menu date
        items: List of menu items
    """
    date: str
    items: tuple[MenuItem, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Student:
    """
    Represents a student enrolled in a class.
    
    Attributes:
        id: Student ID (from data-user-id)
        name: First name
        surname: Last name
        image_url: URL to student's profile picture
    """
    id: str
    name: str
    surname: str
    image_url: Optional[str] = None


@dataclass(frozen=True)
class Instructor:
    """
    Represents a course instructor.
    
    Attributes:
        name: Full name of the instructor
        image_url: URL to instructor's photo
    """
    name: str
    image_url: Optional[str] = None


@dataclass(frozen=True)
class ClassDetail:
    """
    Detailed information about a specific class.
    
    Attributes:
        exams: List of exams and scores
        students: List of enrolled students
        instructor: Course instructor info
        class_average: Main class average (usually final)
        letter_grade: User's letter grade for this class
    """
    exams: tuple[Exam, ...] = field(default_factory=tuple)
    students: tuple[Student, ...] = field(default_factory=tuple)
    instructor: Optional[Instructor] = None
    class_average: Optional[str] = None
    letter_grade: Optional[str] = None
