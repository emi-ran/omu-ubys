# UBYS (OMÜ) Unofficial API - Tam Dokümantasyon

Bu belge, Ondokuz Mayıs Üniversitesi UBYS sistemi için kapsamlı bir API referansıdır. Backend kodlarının analiziyle oluşturulmuştur.

---

## 📋 İçindekiler

1. [Genel Bilgiler](#1-genel-bilgiler)
2. [HTTP Headerları](#2-http-headerları)
3. [Kimlik Doğrulama](#3-kimlik-doğrulama-authentication)
4. [Kullanıcı Profili](#4-kullanıcı-profili)
5. [Danışman Bilgisi](#5-danışman-bilgisi)
6. [Ders Notları](#6-ders-notları-grades)
7. [Detaylı Not Bilgisi](#7-detaylı-not-bilgisi)
8. [Transkript](#8-transkript)
9. [Ders Programı](#9-ders-programı-weekly-schedule)
10. [Ders Detayları](#10-ders-detayları-haftalık-konular)
11. [Yemekhane Menüsü](#11-yemekhane-menüsü)
12. [Hata Kodları ve Çözümler](#12-hata-kodları-ve-çözümler)
13. [Veri Tipleri](#13-veri-tipleri-typescript-interfaces)
14. [Python Örnek Kod](#14-python-örnek-kod)

---

## 1. Genel Bilgiler

| Özellik              | Değer                     |
| -------------------- | ------------------------- |
| **Base URL**         | `https://ubys.omu.edu.tr` |
| **Protokol**         | HTTPS (TLS 1.2+)          |
| **Session Yönetimi** | Cookie tabanlı (ASP.NET)  |
| **Kritik Cookie**    | `ASP.NET_SessionId`       |

### Önemli Notlar

- Tüm işlemlerde `ASP.NET_SessionId` çerezinin korunması zorunludur.
- Session timeout süresi hareketsizlik durumunda yaklaşık 20-30 dakikadır.
- İstemci (Client) tarafında stateful (session koruyan) bir yapı kullanılmalıdır.

---

## 2. HTTP Headerları

### Zorunlu Headerlar (Tüm İstekler)

Tarayıcıyı taklit etmek(impersonation) için bu headerlar **zorunludur**.

```http
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
Accept-Language: tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7
Accept-Encoding: gzip, deflate, br
Connection: keep-alive
Sec-Ch-Ua: "Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"
Sec-Ch-Ua-Mobile: ?0
Sec-Ch-Ua-Platform: "Windows"
```

### AJAX İstekleri İçin Ek Header

JSON döndüren veya sayfa yenilemesi yapmayan endpointler için (Login, Ders Programı, Danışman Bilgisi vb.):

```http
X-Requested-With: XMLHttpRequest
```

### Sayfa Navigasyonu İçin

Tam sayfa yüklemelerinde (Profil, Notlar, Transkript):

```http
Upgrade-Insecure-Requests: 1
Sec-Fetch-Dest: document
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: same-origin
Sec-Fetch-User: ?1
```

---

## 3. Kimlik Doğrulama (Authentication)

### Adım 1: CSRF Token Alma

**Request:**

```http
GET / HTTP/1.1
Host: ubys.omu.edu.tr
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
```

**İşlem:**
HTML yanıtı içindeki hidden input'tan token parse edilir:

```html
<input name="__RequestVerificationToken" type="hidden" value="TOKEN_DEGERI" />
```

### Adım 2: Login İsteği

**Request:**

```http
POST /Account/Login HTTP/1.1
Host: ubys.omu.edu.tr
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
X-Requested-With: XMLHttpRequest
Referer: https://ubys.omu.edu.tr/
```

**Body (Form Data):**

```
__RequestVerificationToken=<TOKEN_ADIM_1>&username=<OGRENCI_NO>&password=<SIFRE>&X-Requested-With=XMLHttpRequest
```

**Başarılı Yanıt (200 OK):**

```json
{
  "longUsername": "AD SOYAD",
  "direct": "/AIS/Student/Home/Index",
  "errorType": null,
  "errorMessage": null
}
```

---

## 4. Kullanıcı Profili

**Endpoint:** `GET /AIS/Student/Home/Index`

**Referer:** `https://ubys.omu.edu.tr/`

### Veri Çıkarma (Scraping)

#### 4.1 Kritik ID'ler (Base64 Encoded JSON)

Sayfa kaynağında `StudentInfo` değişkeni aranır.
**Regex:** `StudentInfo\s*=\s*JSON\.parse\(Base64\.decode\("([^"]+)"\)\)`

**JSON İçeriği:**

```json
{
  "StudentId": 123456, // --> DB Student ID (Ders programı için)
  "Programs": [
    {
      "StudentAcademicProgramId": 999,
      "EducationSemester": 5,
      "RecordSemester": 2, // --> Dönem ID (Ders programı için)
      "RecordYear": 2024 // --> Yıl (Ders programı için)
    }
  ]
}
```

#### 4.2 SAP ID (Program ID)

Menüdeki program seçimi linkinden alınır.
**Regex:** `selectAcademicProgram\('([^']+)'\)` -> `8sQkjaPc...` (Bu ID notları çekmek için şarttır)

---

## 5. Danışman Bilgisi

**Endpoint:** `GET /AIS/Student/Home/AdvisorInfo?sapId=<SAP_ID>`

**Headers:** `X-Requested-With: XMLHttpRequest`

**Parsing:**
HTML içinde `h5` etiketinde "Danışman" yazan kutucuk bulunur.

- İsim: `dt:contains("Ad Soyad:")` kardeş elementinden (`dd`) alınır.
- Email: `dt:contains("E-Mail")` kardeş elementinden (`dd`) alınır.

---

## 6. Ders Notları (Grades)

**Endpoint:** `GET /AIS/Student/Class/Index?sapid=<SAP_ID>&history=true`

**Parametreler:** `history=true` parametresi tüm geçmiş dönemleri getirir.

**Parsing:**

- `.panel.panel-default`: Her bir dönem paneli.
- `table tbody tr`: Ders satırları.
  - `rowspan="2"` olan satırlar ana ders satırıdır.
  - Hemen altındaki satır sınav detaylarını içerir.
- **ClassId Parse Etme:** Ders adının olduğu `a` elementinin `href` özelliğinde `classId=...` bulunur. Bu ID url-encoded olabilir.

---

## 7. Detaylı Not Bilgisi

Bir dersin daha detaylı sınav sonuçları (sınıf ortalaması vb.) için kullanılır.

**Endpoint:** `GET /AIS/Student/Class/ClassDetail?classId=<ENCODED_CLASS_ID>`

**Önemli:** `ClassId` parametresindeki `!` karakteri `%21` olarak encode edilmelidir.

**Parsing:**

- `.success-status`: Geçme notu ve harf notu.
- `.table-responsive table`: Sınav listesi (Vize, Final, Bütünleme).
- Sütunlar: [Tipy, Ad, Tarih, Not, ..., Sıralama, Ortalama]

---

## 8. Transkript

**Endpoint:** `GET /AIS/Student/Transcript/Index`

**Nasıl Bulunur:** Dashboard sayfasındaki Transkript linkine (`/AIS/Student/Transcript/Index`) istek atılır.

**Parsing:**

- `table[id="test"]`: Dönem tabloları.
- `caption b`: Dönem adı (Örn: "1 . Yarıyıl").
- Dersi alan, kredisi ve harf notu satırlardan okunur.

---

## 9. Ders Programı (Weekly Schedule)

Bu endpoint en karmaşık olanıdır çünkü özel bir JSON payload gerektirir ve yanıt base64 encoded döner.

**Endpoint:** `POST /AIS/Student/Home/GetWeeklySchedule`

**Headers:** `Content-Type: application/json; charset=UTF-8`

**Payload:**

```json
{
  "co": {
    "InstructorId": null,
    "SemesterId": "2", // StudentInfo.Programs[0].RecordSemester
    "StudentId": 123456, // StudentInfo.StudentId (int)
    "WeeklyScheduleType": 1,
    "WorkcenterId": null,
    "Year": 2025, // StudentInfo.Programs[0].RecordYear + 1
    "GetExamPlans": true,
    "IsAnnual": false
  },
  "reportViewType": 0,
  "isPartial": true
}
```

**Parsing:**
Yanıt string içinde javascript kodu olarak döner:
`_weeklySchedulle = JSON.parse(Base64.decode("..."))`
Base64 kısmını regex ile alıp decode edin.

---

## 10. Ders Detayları (Haftalık Konular)

**Endpoint:** `GET /AIS/Student/Class/GetClassDetailPartial`

**Query Parametreleri:**

- `ClassId`: Ders ID'si
- `ClassDetailPartial`: `2` (Haftalık konu tablosu için sabit)

**Parsing:**
Gelen HTML tablosunda `tr` satırlarını dönerek `1.Hafta`, `2.Hafta` içerikleri çekilir.

---

## 11. Yemekhane Menüsü

**Endpoint:** `https://sks.omu.edu.tr/gunun-yemegi/`

**Not:** Bu site bazen SSL hatası verebilir, verify=False ile istek atılması önerilir.
Authentication gerektirmez.

---

## 12. Hata Kodları ve Çözümler

UBYS ile iletişim kurarken karşılaşabileceğiniz yaygın hatalar ve anlamları:

### HTTP Durum Kodları

| Kod                           | Anlamı          | Çözüm                                                                                                               |
| ----------------------------- | --------------- | ------------------------------------------------------------------------------------------------------------------- |
| **200 OK**                    | İşlem Başarılı  | Veriyi parse etmeye devam edin.                                                                                     |
| **302 Found**                 | Yönlendirme     | Genellikle **Session Expired** anlamına gelir. `/Account/Login` sayfasına yönlendiriyorsa tekrar login olmalısınız. |
| **401 Unauthorized**          | Yetkisiz Erişim | Cookie gönderilmemiş veya oturum süresi dolmuş. Tekrar login olun.                                                  |
| **500 Internal Server Error** | Sunucu Hatası   | Login işleminde şifre yanlışsa döner. Ayrıca payload hatalıysa (Weekly Schedule) dönebilir.                         |
| **503 Service Unavailable**   | Servis Kapalı   | UBYS bakımda olabilir veya aşırı yüklenmiş olabilir.                                                                |

### Uygulama Hataları (JSON Response)

Login endpoint'i 500 dönse bile body içinde detay verebilir:

```json
{
  "errorType": "error",
  "errorMessage": "Kullanıcı adı veya şifre hatalı."
}
```

### Sık Karşılaşılan Sorunlar

1.  **Empty Response / Parsing Hatası**:

    - **Sebep:** Session süresi dolmuş olabilir ancak sunucu 200 dönüp login sayfası HTML'i gönderiyor olabilir.
    - **Kontrol:** Yanıtın `<!DOCTYPE html>` içerip içermediğini veya beklenen JSON yapısında olup olmadığını kontrol edin. Eğer JSON beklerken HTML geliyorsa, session düşmüştür.

2.  **CSRF Token Hatası**:

    - **Sebep:** Login isteği atarken `__RequestVerificationToken` gönderilmemiş veya cookie ile eşleşmiyor.
    - **Çözüm:** Önce ana sayfaya GET isteği atıp token'ı ve cookie'leri tazeleyin, sonra aynı session ile POST atın.

3.  **Base64 Decode Hatası**:
    - **Sebep:** Karakter kodlaması (UTF-8) hatası.
    - **Çözüm:** Python'da `base64.b64decode(str).decode('utf-8')` şeklinde decode edin.

---

## 13. Veri Tipleri (TypeScript Interfaces)

Referans amaçlı TypeScript arayüzleri:

```typescript
interface UserProfile {
  name: string;
  studentNumber: string;
  faculty: string;
  department: string;
  sapId?: string;
  dbStudentId?: number;
}

interface GradeCourse {
  courseCode: string; // BİL101
  courseName: string; // Fizik I
  letterGrade: string; // AA
  status: string; // Başarılı
  exams: GradeExam[];
}

interface ScheduleItem {
  day: string; // Pazartesi
  startTime: string; // 09:00
  endTime: string; // 09:45
  courseName: string;
  classroom: string;
}
```

---

## 14. Python Örnek Kod

```python
import requests
import re
import json
import base64
from urllib.parse import unquote

class UBYS:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        })
        self.base_url = "https://ubys.omu.edu.tr"

    def login(self):
        # 1. Sayfayı Getir & Token Al
        r = self.session.get(self.base_url)
        token = re.search(r'name="__RequestVerificationToken".*?value="([^"]+)"', r.text).group(1)

        # 2. Login Ol
        payload = {
            '__RequestVerificationToken': token,
            'username': self.username,
            'password': self.password,
            'X-Requested-With': 'XMLHttpRequest'
        }
        r = self.session.post(f"{self.base_url}/Account/Login", data=payload)

        if "errorType" in r.text and '"error"' in r.text:
            raise Exception("Giriş başarısız: Kullanıcı adı veya şifre hatalı")

        print("Giriş başarılı.")

    def get_profile(self):
        r = self.session.get(f"{self.base_url}/AIS/Student/Home/Index")

        # Session kontrolü (Hata Yönetimi Örneği)
        if "Account/Login" in r.url:
            raise Exception("Session expired, lütfen tekrar login olun.")

        # StudentInfo (Base64 JSON) yakala
        match = re.search(r'StudentInfo\s*=\s*JSON\.parse\(Base64\.decode\("([^"]+)"\)\)', r.text)
        if match:
            b64_str = match.group(1)
            json_str = base64.b64decode(b64_str).decode('utf-8')
            return json.loads(json_str)
        return None

# Kullanım
client = UBYS("221234", "sifre")
try:
    client.login()
    info = client.get_profile()
    print(info)
except Exception as e:
    print(f"Hata: {e}")
```
