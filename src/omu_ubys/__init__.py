"""
OMU-UBYS - Unofficial Python Client for OMU UBYS

An unofficial Python library for accessing Ondokuz Mayıs University's
Student Information System (UBYS).

DISCLAIMER:
    This is an UNOFFICIAL project and is NOT affiliated with
    Ondokuz Mayıs University in any way. This library is for
    EDUCATIONAL and TESTING purposes only. Use at your own risk.

Quick Start:
    >>> from omu_ubys import UBYSClient
    >>> 
    >>> client = UBYSClient()
    >>> client.login("student_number", "password")
    >>> 
    >>> # Get student profile
    >>> profile = client.get_profile()
    >>> 
    >>> # Get grades
    >>> grades = client.get_grades()
    >>> 
    >>> # Get weekly schedule
    >>> schedule = client.get_weekly_schedule()
    >>> 
    >>> # Don't forget to close
    >>> client.close()

Using Context Manager:
    >>> with UBYSClient("student_number", "password") as client:
    ...     print(client.get_profile().name)
"""

__version__ = "1.0.4"
__author__ = "Emirhan"
__license__ = "MIT"

from .client import UBYSClient
from .models import (
    UserProfile,
    Advisor,
    Course,
    Exam,
    Semester,
    ScheduleItem,
    WeeklyTopic,
    MenuItem,
    CafeteriaMenu,
)
from .exceptions import (
    UBYSError,
    LoginError,
    SessionExpiredError,
    CSRFTokenError,
    ParseError,
    NetworkError,
)

__all__ = [
    # Main client
    "UBYSClient",
    
    # Models
    "UserProfile",
    "Advisor",
    "Course",
    "Exam",
    "Semester",
    "ScheduleItem",
    "WeeklyTopic",
    "MenuItem",
    "CafeteriaMenu",
    
    # Exceptions
    "UBYSError",
    "LoginError",
    "SessionExpiredError",
    "CSRFTokenError",
    "ParseError",
    "NetworkError",
]
