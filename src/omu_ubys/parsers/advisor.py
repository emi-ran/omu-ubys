"""
Advisor Parser

Extracts academic advisor information from UBYS.
"""

from typing import Optional
from bs4 import BeautifulSoup

from ..models import Advisor
from ..exceptions import ParseError


def parse_advisor(html: str) -> Optional[Advisor]:
    """
    Parse advisor information from the AdvisorInfo page.
    
    Args:
        html: HTML content of the advisor info response
        
    Returns:
        Advisor: Advisor information or None if not found
        
    Example:
        >>> advisor = parse_advisor(html)
        >>> if advisor:
        ...     print(f"Advisor: {advisor.name} ({advisor.email})")
    """
    if "Account/Login" in html:
        raise ParseError("Session expired. Please login again.")
    
    soup = BeautifulSoup(html, "lxml")
    
    name = None
    email = None
    
    # Find all dt elements and look for advisor info
    for dt in soup.find_all("dt"):
        dt_text = dt.get_text(strip=True)
        
        # Look for "Ad Soyad:" (exact match from UBYS)
        if "Ad Soyad" in dt_text:
            dd = dt.find_next_sibling("dd")
            if dd and not name:  # Take first occurrence
                name = dd.get_text(strip=True)
        
        # Look for "E-Mail" or "E-Mail :"
        elif "Mail" in dt_text or "E-Posta" in dt_text:
            dd = dt.find_next_sibling("dd")
            if dd and not email:  # Take first occurrence
                email = dd.get_text(strip=True)
                # Also check for mailto link
                link = dd.find("a")
                if link and link.get("href", "").startswith("mailto:"):
                    email = link.get("href").replace("mailto:", "")
    
    if name:
        return Advisor(name=name, email=email)
    
    return None
