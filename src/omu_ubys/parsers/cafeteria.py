"""
Cafeteria Menu Parser

Extracts daily menu from OMU SKS website.
Note: This endpoint does not require authentication.
"""

from typing import Optional
from bs4 import BeautifulSoup

from ..models import CafeteriaMenu, MenuItem


CAFETERIA_URL = "https://sks.omu.edu.tr/gunun-yemegi/"


def parse_cafeteria_menu(html: str) -> Optional[CafeteriaMenu]:
    """
    Parse cafeteria menu from SKS website.
    
    Args:
        html: HTML content of the cafeteria menu page
        
    Returns:
        CafeteriaMenu: Today's menu or None if not found
        
    Example:
        >>> menu = parse_cafeteria_menu(html)
        >>> if menu:
        ...     for item in menu.items:
        ...         print(f"- {item.name}")
    """
    soup = BeautifulSoup(html, "lxml")
    
    items = []
    date_str = ""
    
    # Try to find the date
    # Look for common date patterns in headers or entry titles
    for elem in soup.find_all(["h1", "h2", "h3", "h4", ".entry-title"]):
        text = elem.get_text(strip=True)
        if any(month in text.lower() for month in 
               ["ocak", "şubat", "mart", "nisan", "mayıs", "haziran",
                "temmuz", "ağustos", "eylül", "ekim", "kasım", "aralık"]):
            date_str = text
            break
    
    # Find menu items
    # Common patterns: ul/li lists, table rows, or paragraph text
    
    # Try list format
    for ul in soup.find_all("ul"):
        for li in ul.find_all("li"):
            text = li.get_text(strip=True)
            if text and len(text) > 2:  # Skip very short items
                items.append(MenuItem(name=text))
    
    # If no list items, try table format
    if not items:
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cells = row.find_all(["td", "th"])
                for cell in cells:
                    text = cell.get_text(strip=True)
                    if text and len(text) > 2:
                        items.append(MenuItem(name=text))
    
    # If still no items, try paragraphs or divs with class containing "menu" or "yemek"
    if not items:
        for elem in soup.find_all(["p", "div"]):
            class_str = " ".join(elem.get("class", []))
            if "menu" in class_str.lower() or "yemek" in class_str.lower():
                text = elem.get_text(strip=True)
                if text:
                    # Split by common separators
                    for item_text in text.split("\n"):
                        item_text = item_text.strip()
                        if item_text and len(item_text) > 2:
                            items.append(MenuItem(name=item_text))
    
    # Content area fallback
    if not items:
        content = soup.find(class_="entry-content") or soup.find("article")
        if content:
            for p in content.find_all("p"):
                text = p.get_text(strip=True)
                if text and len(text) > 2:
                    items.append(MenuItem(name=text))
    
    if items:
        return CafeteriaMenu(date=date_str or "Bugün", items=tuple(items))
    
    return None
