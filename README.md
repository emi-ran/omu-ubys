# 📚 OMU-UBYS

<div align="center">

**Unofficial Python client for OMU UBYS (University Information Management System)**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/omu-ubys.svg)](https://badge.fury.io/py/omu-ubys)

[TR | Türkçe Dokümantasyon](https://github.com/emi-ran/omu-ubys/blob/main/README_TR.md)

</div>

---

> ⚠️ **DISCLAIMER**: This is an **UNOFFICIAL** project and is **NOT** affiliated with Ondokuz Mayıs University. For **EDUCATIONAL and TESTING purposes only**.

---

## 🚀 Installation

```bash
pip install omu-ubys
```

## 📖 Quick Start

```python
from omu_ubys import UBYSClient

with UBYSClient("student_number", "password") as client:
    profile = client.get_profile()
    print(f"Welcome {profile.name}! GPA: {profile.gano}")
```

---

## 📋 API Reference

| Method                                        | Description                           | Returns              |
| --------------------------------------------- | ------------------------------------- | -------------------- |
| [`get_profile()`](#-profile)                  | Student profile with cumulative GPA   | `UserProfile`        |
| [`get_transcript()`](#-transcript)            | Academic transcript with semester GPA | `list[Semester]`     |
| [`get_grades()`](#-grades)                    | Course grades and exam details        | `list[Semester]`     |
| [`get_weekly_schedule()`](#️-weekly-schedule) | Weekly class schedule                 | `list[ScheduleItem]` |
| [`get_advisor()`](#-advisor)                  | Academic advisor info                 | `Advisor`            |
| [`get_cafeteria_menu()`](#-cafeteria-menu)    | Today's menu _(no auth required)_     | `CafeteriaMenu`      |

---

## 🔍 Usage Examples

### 👤 Profile

```python
profile = client.get_profile()
print(f"Name: {profile.name}")
print(f"GPA: {profile.gano}")
```

<details>
<summary>📦 <b>UserProfile Structure</b></summary>

```python
UserProfile(
    name="Emirhan Çetinkaya",
    student_number="24060371",
    faculty="Faculty of Engineering",
    department="Computer Engineering",
    gano=2.61,           # Cumulative GPA
    year=2,
    sap_id="...",
    db_student_id="..."
)
```

</details>

---

### 📜 Transcript

```python
transcript = client.get_transcript()
for sem in transcript:
    print(f"{sem.name}: GPA={sem.gpa}")
```

<details>
<summary>📦 <b>Semester Structure</b></summary>

```python
Semester(
    name="1 . Yarıyıl",
    gpa=2.93,            # Semester GPA
    courses=(
        Course(code="BİL101", name="Programming I", credit=4.0, letter_grade="CB"),
        Course(code="MAT101", name="Mathematics I", credit=4.0, letter_grade="BB"),
        ...
    )
)
```

</details>

---

### 📊 Grades

```python
grades = client.get_grades()
for sem in grades:
    for course in sem.courses:
        print(f"{course.code}: {course.letter_grade}")

        # Use class_id for exam details
        if course.class_id:
            details = client.get_class_details(course.class_id)
```

<details>
<summary>📦 <b>Course and Exam Structure</b></summary>

```python
Course(
    code="BİL101",
    name="Programming I",
    credit=4.0,
    letter_grade="CB",
    status="Başarılı",
    class_id="12345",    # Use for exam details
    exams=(
        Exam(exam_type="Vize", name="Midterm 1", score=75.0, average=65.0),
        Exam(exam_type="Final", name="Final", score=80.0, average=70.0),
    )
)
```

</details>

---

### 🗓️ Weekly Schedule

```python
schedule = client.get_weekly_schedule()
for item in schedule:
    print(f"{item.day} {item.start_time}: {item.course_name} @ {item.classroom}")
```

<details>
<summary>📦 <b>ScheduleItem Structure</b></summary>

```python
ScheduleItem(
    day="Pazartesi",
    start_time="09:00",
    end_time="09:50",
    course_name="Data Structures",
    course_code="BİL201",
    classroom="D-201",
    instructor="Prof. Dr. ..."
)
```

</details>

---

### 👨‍🏫 Advisor

```python
advisor = client.get_advisor()
if advisor:
    print(f"{advisor.name} - {advisor.email}")
```

---

### 🍽️ Cafeteria Menu

> **Note:** This method works without authentication!

```python
menu = UBYSClient().get_cafeteria_menu()
if menu:
    for item in menu.items:
        print(f"• {item.name} ({item.calories} kcal)")
```

---

## ⚠️ Error Handling

```python
from omu_ubys import UBYSClient, LoginError, NetworkError, SessionExpiredError

try:
    client.login("number", "password")
except LoginError:
    print("Invalid username or password")
except NetworkError:
    print("Connection error")
except SessionExpiredError:
    print("Session expired")
```

---

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.

---

<div align="center">
Made with ❤️ for OMU students
</div>
