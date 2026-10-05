# Data Dictionary

This document defines every field used across all sources, the final dataset, and the scraped web data.

---

## 📌 Overview

The dataset is assembled from **four sources**:

1. **CSV** — base student records
2. **REST API** — enrichment fields
3. **SQLite** — course enrollments
4. **HTML (Web Scraping)** — supplementary data (Unit 7)

Integrated via `student_id`. Stored in **SQLite** (relational) and **MongoDB** (semi-structured).

---

## 1️⃣ CSV Source: `data/raw/students.csv`

| Column | Type | Required | Description | Constraints | Example |
|--------|------|----------|-------------|-------------|---------|
| `student_id` | INTEGER | ✅ | Unique identifier | Unique, positive | `1001` |
| `name` | TEXT | ✅ | Full name | Min 2 chars | `Ahmed Ali` |
| `age` | INTEGER | ✅ | Age in years | 16 ≤ age ≤ 80 | `22` |
| `email` | TEXT | ✅ | Email address | Valid format | `ahmed@example.com` |
| `phone` | TEXT | ✅ | Contact number | 9–15 digits | `777123456` |

---

## 2️⃣ API Source: `http://127.0.0.1:5000/students`

| Column | Type | Required | Description | Constraints | Example |
|--------|------|----------|-------------|-------------|---------|
| `student_id` | INTEGER | ✅ | Merge key | Must match CSV | `1001` |
| `gpa` | REAL | ✅ | Grade Point Average | 0.0 ≤ gpa ≤ 4.0 | `3.45` |
| `attendance` | REAL | ✅ | Attendance % | 0 ≤ attendance ≤ 100 | `92.5` |
| `status` | TEXT | ✅ | Status | `Active` / `Inactive` | `Active` |

---

## 3️⃣ SQLite Source: `enrollments` + `courses`

| Column | Type | Required | Description | Example |
|--------|------|----------|-------------|---------|
| `student_id` | INTEGER | ✅ | Merge key | `1001` |
| `course_id` | INTEGER | ✅ | Course identifier | `1` |
| `course_name` | TEXT | ✅ | Course name | `Python Programming` |
| `credit_hours` | INTEGER | ⚠️ | Credit hours | `3` |
| `semester` | TEXT | ⚠️ | Semester label | `2026-1` |
| `score` | REAL | ⚠️ | Course score | `88.0` |

---

## 4️⃣ Web Scraping Source: `data/raw/web_students.html`

Scraped by `src/scraper.py`. Saves to `data/processed/web_students.csv`.

| Column | Type | Required | Description | Constraints | Example |
|--------|------|----------|-------------|-------------|---------|
| `student_id` | INTEGER | ✅ | Student ID | Positive | `2001` |
| `name` | TEXT | ✅ | Student name | Min 2 chars | `Ali Hassan` |
| `city` | TEXT | ⚠️ | City of residence | — | `Sanaa` |
| `gpa` | REAL | ⚠️ | GPA | 0.0 ≤ gpa ≤ 4.0 | `3.75` |
| `skills` | TEXT | ⚠️ | Comma-separated skills | — | `Python, SQL` |
| `source` | TEXT | ✅ | Provenance label | `web_scraping` | `web_scraping` |
| `source_url` | TEXT | ✅ | HTML file path | — | `data/raw/web_students.html` |
| `retrieved_at` | TEXT | ✅ | UTC timestamp | ISO 8601 | `2026-10-05T16:47:01+00:00` |

**Reference:** Unit 7 — pages 45-63.

---

## 📤 Final Dataset: `data/processed/final_dataset.csv`

Left join of CSV + API + SQLite on `student_id`.

### Column Order

```text
student_id, name, age, email, phone,
attendance, gpa, status,
course_id, course_name, credit_hours, semester, score,
source, source_url, retrieved_at
```

### Rules

- CSV is the base.
- API/enrollment fields may be empty.
- Students may appear multiple times (multiple enrollments).

### Provenance Columns

| Column | Type | Description |
|--------|------|-------------|
| `source` | TEXT | e.g., `csv+api+database` |
| `source_url` | TEXT | `multi-source` |
| `retrieved_at` | TEXT | UTC ISO 8601 |

---

## 🍃 MongoDB Storage (Unit 8)

- **Database:** `university_ai`
- **Collection:** `students`
- **Index:** compound unique `(student_id, course_id)`

Each document mirrors a `final_dataset.csv` row with same field names and BSON types.

**BSON Types:**

| Field | BSON Type |
|-------|-----------|
| `_id` | ObjectId |
| `student_id` | Int32 |
| `name` | String |
| `gpa` | Double |
| `attendance` | Double |
| `status` | String |
| `course_id` | Int32 / Null |
| `source` | String |
| `retrieved_at` | String |

**Reference:** Unit 8 — pages 8-14, 47-51.

---

## 🔢 Data Types Reference

| Type | Description | Example |
|------|-------------|---------|
| INTEGER | Whole numbers | `1001` |
| REAL | Floating point | `3.45` |
| TEXT | Strings | `Ahmed Ali` |
| TIMESTAMP | ISO 8601 UTC | `2026-10-05T08:53:17+00:00` |

---

## 🚫 Controlled Values

| Field | Allowed Values |
|-------|---------------|
| `status` | `Active`, `Inactive` |
| `semester` | `YYYY-N` (e.g., `2026-1`) |
| `source` | `csv+api+database`, `web_scraping` |

---

## 🗂️ Generated Files

| File | Contents |
|------|----------|
| `data/raw/students.csv` | Original CSV |
| `data/raw/students_raw_backup.csv` | CSV snapshot |
| `data/raw/api_response.json` | Raw API JSON |
| `data/raw/web_students.html` | HTML source for scraping |
| `data/staging/extracted_students.csv` | Staging copy |
| `data/processed/valid_students.csv` | Valid CSV rows |
| `data/processed/final_dataset.csv` | Final integrated |
| `data/processed/web_students.csv` | Scraped data |
| `data/processed/students.db` | SQLite DB |
| `data/rejected/rejected_records.csv` | Rejected rows |
| MongoDB `university_ai.students` | Semi-structured mirror |

---

## 📚 Related Documents

- [`schema.md`](schema.md)
- [`pipeline.md`](pipeline.md)
- [`validation_rules.md`](validation_rules.md)
- [`../README.md`](../README.md)

---

## 📌 Notes

- All timestamps UTC.
- Missing numerics → median.
- Duplicate `student_id` removed (first kept).
- Same data in SQLite + MongoDB.
- Web data preserved separately (not merged).
- Follows Unit 7, 8, 11 specifications.