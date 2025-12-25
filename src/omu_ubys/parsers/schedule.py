"""
Schedule Parser

Extracts weekly schedule from UBYS.
"""

import re
import json
import base64
from typing import List

from ..models import ScheduleItem
from ..exceptions import ParseError


def parse_weekly_schedule(response_text: str) -> List[ScheduleItem]:
    """
    Parse weekly schedule from the GetWeeklySchedule response.
    
    The response contains JavaScript code with Base64-encoded JSON.
    
    Args:
        response_text: Raw response text from GetWeeklySchedule endpoint
        
    Returns:
        list[ScheduleItem]: List of schedule items
        
    Raises:
        ParseError: If parsing fails
        
    Example:
        >>> schedule = parse_weekly_schedule(response)
        >>> for item in schedule:
        ...     print(f"{item.day} {item.start_time}: {item.course_name}")
    """
    # Find Base64 encoded schedule data
    pattern = r'_weeklySchedulle\s*=\s*JSON\.parse\(Base64\.decode\("([^"]+)"\)\)'
    match = re.search(pattern, response_text)
    
    if not match:
        # Try alternative patterns
        alt_pattern = r'JSON\.parse\(Base64\.decode\("([^"]+)"\)\)'
        match = re.search(alt_pattern, response_text)
    
    if not match:
        raise ParseError("Could not find schedule data in response")
    
    try:
        b64_string = match.group(1)
        json_string = base64.b64decode(b64_string).decode("utf-8")
        data = json.loads(json_string)
    except Exception as e:
        raise ParseError(f"Failed to decode schedule data: {e}") from e
    
    return _parse_schedule_data(data)


def _parse_schedule_data(data) -> List[ScheduleItem]:
    """
    Parse the decoded schedule JSON into ScheduleItem objects.
    
    UBYS returns an array of schedule objects, each containing an Events array.
    """
    items = []
    
    # Day mapping (DayOfWeek: 1=Monday, 5=Friday, etc.)
    day_map = {
        1: "Pazartesi",
        2: "Salı",
        3: "Çarşamba",
        4: "Perşembe",
        5: "Cuma",
        6: "Cumartesi",
        7: "Pazar",
    }
    
    # Handle the array of schedule objects
    if isinstance(data, list):
        for schedule_obj in data:
            if not isinstance(schedule_obj, dict):
                continue
            
            # Events are inside each schedule object
            events = schedule_obj.get("Events", [])
            
            for event in events:
                if not isinstance(event, dict):
                    continue
                
                # Extract day
                day_index = event.get("DayOfWeek", 0)
                day = day_map.get(day_index, f"Gün {day_index}")
                
                # Extract time - format as HH:MM
                start_hour = event.get("StartHour", 0)
                start_minute = event.get("StartMinute", 0)
                finish_hour = event.get("FinishHour", 0)
                finish_minute = event.get("FinishMinute", 0)
                
                start_time = f"{start_hour:02d}:{start_minute:02d}"
                end_time = f"{finish_hour:02d}:{finish_minute:02d}"
                
                # Extract course info
                course_name = event.get("CourseName", "")
                classroom = event.get("WorkCenterName", "")
                instructor = event.get("InstructorName", "")
                
                # Clean up instructor name (may have newlines)
                if instructor:
                    instructor = instructor.replace("\r\n", " ").replace("\n", " ").strip()
                
                # Extract course code from CourseName if present
                # Format: "BİL103.1 Programlamaya Giriş - I"
                course_code = None
                if course_name and " " in course_name:
                    parts = course_name.split(" ", 1)
                    if len(parts[0]) <= 10:  # Reasonable course code length
                        course_code = parts[0]
                
                items.append(ScheduleItem(
                    day=day,
                    start_time=start_time,
                    end_time=end_time,
                    course_name=course_name,
                    course_code=course_code,
                    classroom=classroom or None,
                    instructor=instructor or None,
                ))
    
    # Sort by day and time
    day_order = {v: k for k, v in day_map.items()}
    items.sort(key=lambda x: (day_order.get(x.day, 99), x.start_time))
    
    # Deduplicate - same course on same day/time appears for each week
    seen = set()
    unique_items = []
    for item in items:
        key = (item.day, item.start_time, item.end_time, item.course_name)
        if key not in seen:
            seen.add(key)
            unique_items.append(item)
    
    return unique_items


def _parse_days_format(data: dict) -> List[ScheduleItem]:
    """Parse alternative schedule format with Days array."""
    items = []
    days = data.get("Days", [])
    
    day_names = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    
    for day_index, day_data in enumerate(days):
        if not isinstance(day_data, dict):
            continue
        
        day_name = day_names[day_index] if day_index < len(day_names) else f"Gün {day_index}"
        slots = day_data.get("Slots", day_data.get("slots", []))
        
        for slot in slots:
            if not slot:
                continue
            
            items.append(ScheduleItem(
                day=day_name,
                start_time=slot.get("StartTime", ""),
                end_time=slot.get("EndTime", ""),
                course_name=slot.get("CourseName", ""),
                course_code=slot.get("CourseCode"),
                classroom=slot.get("Classroom"),
                instructor=slot.get("Instructor"),
            ))
    
    return items
