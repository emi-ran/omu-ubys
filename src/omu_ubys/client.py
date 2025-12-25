"""
OMU-UBYS Python Client

An unofficial Python library for accessing OMU UBYS (University Information Management System).

DISCLAIMER:
    This is an UNOFFICIAL library and is NOT affiliated with Ondokuz Mayıs University.
    This project is for EDUCATIONAL and TESTING purposes only.
    Use at your own risk.

Example:
    >>> from omu_ubys import UBYSClient
    >>> 
    >>> client = UBYSClient()
    >>> client.login("student_number", "password")
    >>> 
    >>> profile = client.get_profile()
    >>> print(profile.name)
    >>> 
    >>> grades = client.get_grades()
    >>> for semester in grades:
    ...     print(f"{semester.name}: {len(semester.courses)} courses")
"""

from typing import Optional, List
from urllib.parse import quote

import httpx

from .models import (
    UserProfile,
    Advisor,
    Semester,
    ScheduleItem,
    CafeteriaMenu,
)
from .exceptions import (
    UBYSError,
    LoginError,
    SessionExpiredError,
    ParseError,
    NetworkError,
)
from . import auth
from .parsers import (
    parse_student_info,
    parse_sap_id,
    parse_grades,
    parse_class_detail,
    parse_transcript,
    parse_weekly_schedule,
    parse_advisor,
    parse_cafeteria_menu,
)


class UBYSClient:
    """
    UBYS Client for accessing student data.
    
    This client handles authentication and provides methods to fetch
    various student information from UBYS.
    
    Attributes:
        is_logged_in (bool): Whether the client is currently authenticated
        profile (UserProfile): Cached profile information (after login)
    
    Example:
        Basic usage::
        
            from omu_ubys import UBYSClient
            
            client = UBYSClient()
            client.login("221234567", "password")
            
            # Get profile
            profile = client.get_profile()
            print(f"Welcome, {profile.name}!")
            
            # Get grades
            grades = client.get_grades()
            for semester in grades:
                print(f"\\n{semester.name}:")
                for course in semester.courses:
                    print(f"  {course.code}: {course.letter_grade}")
        
        Using context manager::
        
            with UBYSClient("221234567", "password") as client:
                print(client.get_profile().name)
    """
    
    BASE_URL = "https://ubys.omu.edu.tr"
    CAFETERIA_URL = "https://sks.omu.edu.tr/gunun-yemegi/"
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize the UBYS client.
        
        Args:
            username: Student number (optional, can be provided during login)
            password: Password (optional, can be provided during login)
        """
        self._session: Optional[httpx.Client] = None
        self._username = username
        self._password = password
        self._is_logged_in = False
        
        # Cached data
        self._profile: Optional[UserProfile] = None
        self._sap_id: Optional[str] = None
        self._student_info: Optional[dict] = None
    
    def __enter__(self):
        """Context manager entry - auto login if credentials provided."""
        if self._username and self._password:
            self.login(self._username, self._password)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close session."""
        self.close()
    
    @property
    def is_logged_in(self) -> bool:
        """Check if currently logged in."""
        return self._is_logged_in
    
    @property
    def profile(self) -> Optional[UserProfile]:
        """Get cached profile (None if not logged in)."""
        return self._profile
    
    def _ensure_session(self):
        """Ensure HTTP session exists."""
        if self._session is None:
            self._session = auth.create_session()
    
    def _ensure_logged_in(self):
        """Raise error if not logged in."""
        if not self._is_logged_in:
            raise SessionExpiredError("Not logged in. Call login() first.")
    
    def login(self, username: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        Login to UBYS.
        
        Args:
            username: Student number (uses stored value if not provided)
            password: Password (uses stored value if not provided)
            
        Returns:
            bool: True if login successful
            
        Raises:
            LoginError: If login fails (wrong credentials, etc.)
            NetworkError: If connection fails
            
        Example:
            >>> client = UBYSClient()
            >>> client.login("221234567", "mypassword")
            True
        """
        username = username or self._username
        password = password or self._password
        
        if not username or not password:
            raise LoginError("Username and password are required")
        
        self._ensure_session()
        
        # Perform login
        result = auth.login(self._session, username, password)
        
        self._is_logged_in = True
        self._username = username
        
        # Fetch and cache profile data
        self._fetch_initial_data()
        
        return True
    
    def _fetch_initial_data(self):
        """Fetch initial profile data after login."""
        try:
            response = self._session.get(f"{self.BASE_URL}/AIS/Student/Home/Index")
            html = response.text
            
            # Parse StudentInfo
            self._student_info = parse_student_info(html)
            self._sap_id = parse_sap_id(html)
            
            # Extract data from nested structure
            programs = self._student_info.get("Programs", [])
            person_data = self._student_info.get("Person", {}).get("Person", {})
            
            # StudentId is inside Programs, not top-level
            student_id = None
            semester_id = None
            year = None
            faculty = ""
            department = ""
            gano = None
            
            if programs:
                program = programs[0]
                student_id = program.get("StudentId")
                semester_id = program.get("RecordSemester")
                year = program.get("RecordYear")
                department = program.get("AcademicProgramName", "")
                faculty = program.get("UnitName", "").split(" - ")[0] if program.get("UnitName") else ""
                gano = program.get("GANO")
            
            # Get name from Person
            name = ""
            if person_data:
                first_name = person_data.get("Name", "")
                last_name = person_data.get("Surname", "")
                name = f"{first_name} {last_name}".strip()
            
            self._profile = UserProfile(
                name=name,
                student_number=self._username or "",
                faculty=faculty,
                department=department,
                sap_id=self._sap_id,
                db_student_id=student_id,
                semester_id=semester_id,
                year=year,
                gano=gano,
            )
        except Exception:
            # Non-critical, profile will just be minimal
            pass
    
    def get_profile(self) -> UserProfile:
        """
        Get student profile information.
        
        Returns:
            UserProfile: Student profile with name, number, faculty, etc.
            
        Raises:
            SessionExpiredError: If not logged in
            ParseError: If parsing fails
            
        Example:
            >>> profile = client.get_profile()
            >>> print(profile.name)
            "Ahmet Yılmaz"
            >>> print(profile.student_number)
            "221234567"
        """
        self._ensure_logged_in()
        
        if self._profile:
            return self._profile
        
        self._fetch_initial_data()
        return self._profile
    
    def get_advisor(self) -> Optional[Advisor]:
        """
        Get academic advisor information.
        
        Returns:
            Advisor: Advisor name and email, or None if not found
            
        Raises:
            SessionExpiredError: If not logged in
            ParseError: If parsing fails
            
        Example:
            >>> advisor = client.get_advisor()
            >>> if advisor:
            ...     print(f"Advisor: {advisor.name}")
            ...     print(f"Email: {advisor.email}")
        """
        self._ensure_logged_in()
        
        if not self._sap_id:
            return None
        
        response = self._session.get(
            f"{self.BASE_URL}/AIS/Student/Home/AdvisorInfo",
            params={"sapId": self._sap_id},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        
        return parse_advisor(response.text)
    
    def get_grades(self, include_history: bool = True) -> List[Semester]:
        """
        Get course grades.
        
        Args:
            include_history: If True, includes all past semesters
            
        Returns:
            list[Semester]: List of semesters with courses and grades
            
        Raises:
            SessionExpiredError: If not logged in
            ParseError: If parsing fails
            
        Example:
            >>> grades = client.get_grades()
            >>> for semester in grades:
            ...     print(f"\\n{semester.name}:")
            ...     for course in semester.courses:
            ...         print(f"  {course.code} {course.name}: {course.letter_grade}")
        """
        self._ensure_logged_in()
        
        params = {"history": "true"} if include_history else {}
        if self._sap_id:
            params["sapid"] = self._sap_id
        
        response = self._session.get(
            f"{self.BASE_URL}/AIS/Student/Class/Index",
            params=params,
        )
        
        return parse_grades(response.text)
    
    def get_class_details(self, class_id: str) -> dict:
        """
        Get detailed information for a specific class.
        
        Args:
            class_id: The class ID (obtained from grades)
            
        Returns:
            dict: Detailed class info including exam scores and averages
            
        Raises:
            SessionExpiredError: If not logged in
            ParseError: If parsing fails
            
        Example:
            >>> grades = client.get_grades()
            >>> first_course = grades[0].courses[0]
            >>> if first_course.class_id:
            ...     details = client.get_class_details(first_course.class_id)
            ...     print(details)
        """
        self._ensure_logged_in()
        
        # Encode special characters
        encoded_id = quote(class_id, safe="")
        
        response = self._session.get(
            f"{self.BASE_URL}/AIS/Student/Class/ClassDetail",
            params={"classId": encoded_id},
        )
        
        return parse_class_detail(response.text)
    
    def get_transcript(self) -> List[Semester]:
        """
        Get academic transcript.
        
        Returns:
            list[Semester]: List of semesters with courses, grades, and GPA
            
        Raises:
            SessionExpiredError: If not logged in
            ParseError: If parsing fails
            
        Example:
            >>> transcript = client.get_transcript()
            >>> for semester in transcript:
            ...     print(f"{semester.name}: GPA {semester.gpa}")
        """
        self._ensure_logged_in()
        
        # First, get transcript link from dashboard (it contains required params)
        from bs4 import BeautifulSoup
        
        dashboard_response = self._session.get(f"{self.BASE_URL}/AIS/Student/Home/Index")
        dashboard_soup = BeautifulSoup(dashboard_response.text, "lxml")
        
        # Find transcript link
        transcript_link = dashboard_soup.select_one('a[href*="/AIS/Student/Transcript/Index"]')
        
        if transcript_link:
            href = transcript_link.get("href", "")
            # Clean up HTML entities
            href = href.replace("&amp;", "&")
            transcript_url = f"{self.BASE_URL}{href}" if href.startswith("/") else href
        else:
            # Fallback to manual URL
            transcript_url = f"{self.BASE_URL}/AIS/Student/Transcript/Index"
            if self._sap_id:
                transcript_url += f"?sapId={self._sap_id}"
        
        response = self._session.get(transcript_url)
        
        return parse_transcript(response.text)
    
    def get_weekly_schedule(self) -> List[ScheduleItem]:
        """
        Get weekly course schedule.
        
        Returns:
            list[ScheduleItem]: List of schedule items sorted by day and time
            
        Raises:
            SessionExpiredError: If not logged in
            ParseError: If parsing fails
            
        Example:
            >>> schedule = client.get_weekly_schedule()
            >>> for item in schedule:
            ...     print(f"{item.day} {item.start_time}-{item.end_time}: {item.course_name}")
        """
        self._ensure_logged_in()
        
        if not self._student_info:
            raise ParseError("Student info not available. Try logging in again.")
        
        # Build payload from student info
        programs = self._student_info.get("Programs", [])
        if not programs:
            return []
        
        program = programs[0]
        
        # StudentId is inside Programs, not top-level
        student_id = program.get("StudentId")
        
        payload = {
            "co": {
                "InstructorId": None,
                "SemesterId": str(program.get("RecordSemester", "")),
                "StudentId": student_id,
                "WeeklyScheduleType": 1,
                "WorkcenterId": None,
                "Year": program.get("RecordYear", __import__('datetime').datetime.now().year) + 1,
                "GetExamPlans": True,
                "IsAnnual": False,
            },
            "reportViewType": 0,
            "isPartial": True,
        }
        
        response = self._session.post(
            f"{self.BASE_URL}/AIS/Student/Home/GetWeeklySchedule",
            json=payload,
            headers={"Content-Type": "application/json; charset=UTF-8"},
        )
        
        return parse_weekly_schedule(response.text)
    
    def get_cafeteria_menu(self) -> Optional[CafeteriaMenu]:
        """
        Get today's cafeteria menu.
        
        Note: This method does NOT require authentication.
        
        Returns:
            CafeteriaMenu: Today's menu or None if not available
            
        Example:
            >>> # Can be called without login
            >>> client = UBYSClient()
            >>> menu = client.get_cafeteria_menu()
            >>> if menu:
            ...     print(f"Menu for {menu.date}:")
            ...     for item in menu.items:
            ...         print(f"  - {item.name}")
        """
        # This endpoint doesn't require auth, create temp session if needed
        session = self._session or httpx.Client(
            headers=auth.DEFAULT_HEADERS,
            timeout=30.0,
            verify=False,  # SKS site may have SSL issues
        )
        
        try:
            response = session.get(self.CAFETERIA_URL)
            return parse_cafeteria_menu(response.text)
        except Exception:
            return None
        finally:
            if not self._session:
                session.close()
    
    def close(self):
        """
        Close the HTTP session.
        
        Call this when done using the client, or use context manager.
        """
        if self._session:
            self._session.close()
            self._session = None
        self._is_logged_in = False
