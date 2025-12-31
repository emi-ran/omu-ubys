# 📚 OMU-UBYS

<div align="center">

**OMÜ UBYS (Üniversite Bilgi Yönetim Sistemi) için resmi olmayan Python istemcisi**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/omu-ubys.svg)](https://badge.fury.io/py/omu-ubys)

[EN | English Documentation](https://github.com/emi-ran/omu-ubys/blob/main/README.md)

</div>

---

> ⚠️ **UYARI**: Bu proje **RESMİ DEĞİLDİR** ve Ondokuz Mayıs Üniversitesi ile hiçbir bağı yoktur. Sadece **EĞİTİM ve TEST** amaçlıdır.

---

## 🚀 Kurulum

```bash
pip install omu-ubys
```

## 📖 Hızlı Başlangıç

```python
from omu_ubys import UBYSClient

with UBYSClient("ogrenci_no", "sifre") as client:
    profile = client.get_profile()
    print(f"Hoş geldin {profile.name}! GANO: {profile.gano}")
```

---

## 📋 API Referansı

| Metot                                             | Açıklama                          | Dönüş                |
| ------------------------------------------------- | --------------------------------- | -------------------- |
| [`get_profile()`](#-profil-bilgisi)               | Öğrenci profili ve GANO           | `UserProfile`        |
| [`get_transcript()`](#-transkript)                | Akademik transkript + YANO        | `list[Semester]`     |
| [`get_grades()`](#-notlar)                        | Dönem notları ve sınav detayları  | `list[Semester]`     |
| [`get_class_details(class_id)`](#-ders-detaylari) | Ders detayları ve öğrenci listesi | `ClassDetail`        |
| [`get_weekly_schedule()`](#️-haftalık-program)    | Haftalık ders programı            | `list[ScheduleItem]` |
| [`get_advisor()`](#-danışman)                     | Danışman bilgileri                | `Advisor`            |
| [`get_cafeteria_menu()`](#-yemek-menüsü)          | Günün yemeği _(giriş gerekmez)_   | `CafeteriaMenu`      |

---

## 🔍 Kullanım Örnekleri

### 👤 Profil Bilgisi

```python
profile = client.get_profile()
print(f"Ad: {profile.name}")
print(f"GANO: {profile.gano}")
```

<details>
<summary>📦 <b>UserProfile Yapısı</b></summary>

```python
UserProfile(
    name="Emirhan Çetinkaya",
    student_number="24060371",
    faculty="Mühendislik Fakültesi",
    department="Bilgisayar Mühendisliği",
    gano=2.61,           # Genel Akademik Not Ortalaması
    year=2,
    sap_id="...",
    db_student_id="..."
)
```

</details>

---

### 📜 Transkript

```python
transcript = client.get_transcript()
for sem in transcript:
    print(f"{sem.name}: YANO={sem.gpa}")
```

<details>
<summary>📦 <b>Semester Yapısı</b></summary>

```python
Semester(
    name="1 . Yarıyıl",
    gpa=2.93,            # Yarıyıl Akademik Not Ortalaması (YANO)
    courses=(
        Course(code="BİL101", name="Programlama I", credit=4.0, letter_grade="CB"),
        Course(code="MAT101", name="Matematik I", credit=4.0, letter_grade="BB"),
        ...
    )
)
```

</details>

---

### 📊 Notlar

```python
grades = client.get_grades()
for sem in grades:
    for course in sem.courses:
        print(f"{course.code}: {course.letter_grade}")

        # Sınav detayları için class_id kullan
        if course.class_id:
            details = client.get_class_details(course.class_id)
```

<details>
<summary>📦 <b>Course ve Exam Yapısı</b></summary>

```python
Course(
    code="BİL101",
    name="Programlama I",
    credit=4.0,
    letter_grade="CB",
    status="Başarılı",
    class_id="12345",    # Sınav detayları için kullanılır
    exams=(
        Exam(exam_type="Vize", name="1. Ara Sınav", score=75.0, average=65.0),
        Exam(exam_type="Final", name="Final", score=80.0, average=70.0),
    )
)
```

</details>

---

### 📝 Ders Detayları

```python
# class_id, Course objelerinde mevcuttur (course.class_id)
# get_grades() sonucundan alabilirsiniz
details = client.get_class_details("12345")

print(f"Harf Notu: {details.letter_grade}")
print(f"Sınıf Ortalaması: {details.class_average}")

if details.instructor:
    print(f"Öğretim Görevlisi: {details.instructor.name}")

print(f"Öğrenci Sayısı: {len(details.students)}")
```

<details>
<summary>📦 <b>ClassDetail Yapısı</b></summary>

```python
ClassDetail(
    letter_grade="AA",
    class_average="65.5",
    instructor=Instructor(name="Dr. ...", image_url="..."),
    exams=(
        Exam(exam_type="Vize", score=80.0, ranking="5/50", average=60.0),
        ...
    ),
    students=(
        Student(id="123", name="Ahmet", surname="Yılmaz", image_url="..."),
        ...
    )
)
```

</details>

---

### 🗓️ Haftalık Program

```python
schedule = client.get_weekly_schedule()
for item in schedule:
    print(f"{item.day} {item.start_time}: {item.course_name} @ {item.classroom}")
```

<details>
<summary>📦 <b>ScheduleItem Yapısı</b></summary>

```python
ScheduleItem(
    day="Pazartesi",
    start_time="09:00",
    end_time="09:50",
    course_name="Veri Yapıları",
    course_code="BİL201",
    classroom="D-201",
    instructor="Prof. Dr. ..."
)
```

</details>

---

### 👨‍🏫 Danışman

```python
advisor = client.get_advisor()
if advisor:
    print(f"{advisor.name} - {advisor.email}")
```

---

### 🍽️ Yemek Menüsü

> **Not:** Bu metot giriş yapmadan da çalışır!

```python
menu = UBYSClient().get_cafeteria_menu()
if menu:
    for item in menu.items:
        print(f"• {item.name} ({item.calories} kcal)")
```

---

## ⚠️ Hata Yönetimi

```python
from omu_ubys import UBYSClient, LoginError, NetworkError, SessionExpiredError

try:
    client.login("no", "sifre")
except LoginError:
    print("Hatalı kullanıcı adı veya şifre")
except NetworkError:
    print("Bağlantı hatası")
except SessionExpiredError:
    print("Oturum süresi doldu")
```

---

## 📝 Lisans

MIT Lisansı - Detaylar için [LICENSE](LICENSE) dosyasına bakın.

---

<div align="center">
OMÜ öğrencileri için ❤️ ile yapıldı
</div>
