"""Parsers package for OMU-UBYS."""

from .profile import parse_student_info, parse_sap_id
from .grades import parse_grades, parse_class_detail
from .transcript import parse_transcript
from .schedule import parse_weekly_schedule
from .advisor import parse_advisor
from .cafeteria import parse_cafeteria_menu

__all__ = [
    "parse_student_info",
    "parse_sap_id",
    "parse_grades",
    "parse_class_detail",
    "parse_transcript",
    "parse_weekly_schedule",
    "parse_advisor",
    "parse_cafeteria_menu",
]
