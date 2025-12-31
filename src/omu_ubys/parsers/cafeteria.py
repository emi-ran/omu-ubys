"""
Cafeteria Menu Parser

Extracts daily menu from OMU SKS website.
Note: This endpoint does not require authentication.
"""

from typing import Optional
from bs4 import BeautifulSoup
import re

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
    
    # Find the main content area with the reading class
    reading_div = soup.find("div", class_="reading")
    if not reading_div:
        # Fallback to looking at all content
        reading_div = soup
    
    # Find the first table with has-fixed-layout class (today's menu)
    # Structure: table with rows like: Tarih|31.12.2025, Çorba|Köylü Çorba, etc.
    today_table = reading_div.find("table", class_="has-fixed-layout")
    
    if today_table:
        tbody = today_table.find("tbody")
        if tbody:
            for row in tbody.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    
                    if label.lower() == "tarih":
                        date_str = value
                    elif label and value:
                        # This is a menu item (Çorba, Yemek, Yemek 2, Yemek 3, etc.)
                        items.append(MenuItem(name=value, category=label))
    
    # If no today's menu found, try to find the date header and parse
    if not items:
        # Check for meta date in the page
        meta_date = soup.find("div", class_="meta date")
        if meta_date:
            # Parse date like "31.12.2025"
            date_text = meta_date.get_text(strip=True)
            date_match = re.search(r"\d{2}\.\d{2}\.\d{4}", date_text)
            if date_match:
                date_str = date_match.group()
        
        # Try to find a monthly schedule table and extract today's row
        for table in reading_div.find_all("table"):
            # Skip the has-fixed-layout table we already processed
            if table.get("class") and "has-fixed-layout" in table.get("class"):
                continue
            
            tbody = table.find("tbody")
            if not tbody:
                continue
            
            # Look for header row to understand column structure
            for row in tbody.find_all("tr"):
                cells = row.find_all("td")
                if not cells:
                    continue
                    
                first_cell = cells[0].get_text(strip=True)
                # Check if this row matches the date we're looking for
                if date_str and first_cell == date_str:
                    # Found today's row in monthly schedule
                    for i, cell in enumerate(cells[1:], 1):
                        text = cell.get_text(strip=True)
                        if text:
                            category = f"Yemek {i}" if i > 1 else "Çorba"
                            items.append(MenuItem(name=text, category=category))
                    break
    
    if items:
        return CafeteriaMenu(date=date_str or "Bugün", items=tuple(items))
    
    return None
