"""
Profile Parser

Extracts student profile information from UBYS pages.
"""

import re
import json
import base64
from typing import Optional, Tuple

from ..exceptions import ParseError


def parse_student_info(html: str) -> dict:
    """
    Parse StudentInfo from the home page.
    
    The StudentInfo is stored as a Base64-encoded JSON in the page source.
    
    Args:
        html: HTML content of the student home page
        
    Returns:
        dict: Parsed student info containing StudentId, Programs, etc.
        
    Raises:
        ParseError: If StudentInfo cannot be found or decoded
        
    Example:
        >>> info = parse_student_info(html)
        >>> print(info["StudentId"])
        123456
        >>> print(info["Programs"][0]["EducationSemester"])
        5
    """
    # Find Base64 encoded StudentInfo
    pattern = r'StudentInfo\s*=\s*JSON\.parse\(Base64\.decode\("([^"]+)"\)\)'
    match = re.search(pattern, html)
    
    if not match:
        # Check if redirected to login page
        if "Account/Login" in html or "login-form" in html.lower():
            raise ParseError("Session expired. Please login again.")
        raise ParseError("Could not find StudentInfo in page. Page structure may have changed.")
    
    try:
        b64_string = match.group(1)
        json_string = base64.b64decode(b64_string).decode("utf-8")
        return json.loads(json_string)
    except Exception as e:
        raise ParseError(f"Failed to decode StudentInfo: {e}") from e


def parse_sap_id(html: str) -> Optional[str]:
    """
    Parse the SAP ID (Academic Program ID) from the page.
    
    The SAP ID is needed for fetching grades and other academic data.
    
    Args:
        html: HTML content of the student home page
        
    Returns:
        str or None: The SAP ID if found
        
    Example:
        >>> sap_id = parse_sap_id(html)
        >>> print(sap_id)
        "8sQkjaPc..."
    """
    # SAP ID is in the selectAcademicProgram function call
    pattern = r"selectAcademicProgram\('([^']+)'\)"
    match = re.search(pattern, html)
    
    if match:
        return match.group(1)
    return None


def parse_profile_details(html: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Parse additional profile details from the page.
    
    Args:
        html: HTML content of the student home page
        
    Returns:
        tuple: (name, faculty, department) - any may be None if not found
    """
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html, "lxml")
    
    name = None
    faculty = None
    department = None
    
    # Try to find name from the page header or profile section
    # This varies by page structure, so we try multiple approaches
    
    # Look for common patterns
    profile_div = soup.find("div", class_="profile-info")
    if profile_div:
        name_elem = profile_div.find("h4") or profile_div.find("h3")
        if name_elem:
            name = name_elem.get_text(strip=True)
    
    return name, faculty, department
