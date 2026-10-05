# Pipeline Documentation

This document describes the end-to-end pipeline — including Extract, Transform, Load (SQLite + MongoDB), and Web Scraping.

**Pipeline Type:** Batch ETL + Scraping
**Orchestration:** Manual (`python main.py`)
**Entry Point:** `main.py` → `src/main.py`

---

## 🚀 Execution

```bash
python main.py
```

The mock API is separate:

```bash
python tests/mock_api.py
```

Listens on `http://127.0.0.1:5000/students`.

---

## 📌 Pipeline Overview

```text
┌─────────────┐
│   SOURCE    │  CSV + API + SQLite
└──────┬──────┘
       ▼
┌─────────────┐
│   EXTRACT   │  src/extract.py
└──────┬──────┘
       ▼
┌─────────────┐
│  RAW COPY   │  data/raw/ + data/staging/
└──────┬──────┘
       ▼
┌─────────────┐
│  VALIDATE   │  src/validate.py
└──────┬──────┘
       ▼
┌─────────────┐
│ TRANSFORM   │  src/transform.py
└──────┬──────┘
       ▼
┌─────────────┐
│  FINAL      │  src/validate.py
│  VALIDATE   │
└──────┬──────┘
       ▼
┌─────────────┐     ┌─────────────┐
│    LOAD     │────►│   SQLite    │
│             │     └─────────────┘
│             │     ┌─────────────┐
│             │────►│   MongoDB   │  ← Optional
└──────┬──────┘     └─────────────┘
       ▼
┌─────────────┐
│ WEB SCRAPE  │  src/scraper.py
└──────┬──────┘
       ▼
┌─────────────┐
│   OUTPUT    │  final_dataset.csv + web_students.csv
└─────────────┘
```

---

## 🔄 Pipeline Stages

### 1️⃣ Extract

**File:** `src/extract.py`

| Source | Path / Endpoint |
|--------|-----------------|
| CSV | `data/raw/students.csv` |
| REST API | `http://127.0.0.1:5000/students` |
| SQLite | `data/processed/students.db` |

**Reference:** Unit 7 — pages 7–13.

---

### 2️⃣ Raw Storage

| Output | Path |
|--------|------|
| CSV snapshot | `data/raw/students_raw_backup.csv` |
| API JSON | `data/raw/api_response.json` |
| Staging | `data/staging/extracted_students.csv` |

**Reference:** Unit 7 — page 30.

---

### 3️⃣ Validate CSV Records

**File:** `src/validate.py`

Rules: required columns, non-empty, unique `student_id`, age 16–80, GPA 0–4, attendance 0–100.

Outputs:
- Valid → `data/processed/valid_students.csv`
- Rejected → `data/rejected/rejected_records.csv`

---

### 4️⃣ Transform & Integrate

**File:** `src/transform.py`

Operations: numeric conversion, deduplication, business rules, median imputation, multi-source merge, provenance tagging (`source`, `source_url`, `retrieved_at`).

**Reference:** Unit 10 — pages 26–28; Unit 7 — pages 77–78.

---

### 5️⃣ Final Validation

Re-applies all schema + business rules before loading.

---

### 6️⃣ Load to SQLite

**File:** `src/load.py`

Writes:
- `data/processed/final_dataset.csv`
- `data/processed/students.db`
- `data/processed/valid_students.csv`
- `data/rejected/rejected_records.csv`

**Reference:** Unit 10 — pages 32–33.

---

### 7️⃣ Load to MongoDB (Optional)

**File:** `src/mongo_loader.py`

When `MONGO_ENABLED=true`:
- Database: `university_ai`
- Collection: `students`
- Index: compound unique `(student_id, course_id)`
- Operation: idempotent `upsert`
- Failure: logged, pipeline continues

**Reference:** Unit 8 — pages 29-38, 47-51.

---

### 8️⃣ Web Scraping

**File:** `src/scraper.py`
**Functions:** `read_html_from_file()`, `parse_students_table()`, `scrape_students_from_html()`

Reads `data/raw/web_students.html`, parses with BeautifulSoup, extracts fields:
- `student_id`, `name`, `city`, `gpa`, `skills`

Saves to `data/processed/web_students.csv` with provenance.

**Responsible Scraping** (Unit 7 — pages 53-55):
- Descriptive User-Agent.
- Prefers APIs when available.
- Uses local HTML file for training.
- Respects rate limits.

**Reference:** Unit 7 — pages 42-63.

---

## 📋 Data Lineage

```text
data/raw/students.csv
        ▼
data/raw/students_raw_backup.csv       (preserved)
data/raw/api_response.json             (preserved)
data/staging/extracted_students.csv    (handoff)
        ▼
Pandas DataFrame (in memory)
        ▼
Transformed + Integrated DataFrame (in memory)
        ▼
Validated DataFrame (in memory)
        ├──────────────────────┬──────────────────────┐
        ▼                      ▼                      ▼
data/processed/final_dataset.csv   SQLite: students.db   MongoDB: university_ai.students
        │                                                    │
        └────────────────────┬───────────────────────────────┘
                             ▼
                    ML-ready DataFrame
                             │
                             │
data/raw/web_students.html   │
        ▼                    │
Web Scraping (src/scraper.py)│
        ▼                    │
data/processed/web_students.csv ──┘
```

**Reference:** Unit 7 — page 78; Unit 11 — Section 44.

---

## 🔁 Idempotency & Re-run Behavior

| Artifact | Behavior |
|----------|----------|
| `data/raw/students.csv` | Untouched |
| `data/raw/students_raw_backup.csv` | Overwritten |
| `data/raw/api_response.json` | Overwritten |
| `data/staging/extracted_students.csv` | Overwritten |
| `data/processed/valid_students.csv` | Overwritten |
| `data/processed/final_dataset.csv` | Overwritten |
| `data/processed/web_students.csv` | Overwritten |
| `data/processed/students.db` | Table `students` replaced |
| MongoDB `university_ai.students` | Upserted |
| `data/rejected/rejected_records.csv` | Overwritten |
| `logs/pipeline.log` | Appended |

**Reference:** Unit 10 — Section 23; Unit 8 — pages 35-36.

---

## 🧾 Pipeline Metadata

Unique `batch_id` per run (UTC):

```python
from datetime import datetime, timezone
batch_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
```

---

## 🚨 Error Handling

| Category | Action |
|----------|--------|
| **Recoverable** | Quarantine to `data/rejected/` |
| **Fatal** | Log + raise + stop |
| **Optional MongoDB failure** | Log + continue |
| **Optional Scraper failure** | Log + continue |

**Reference:** Unit 10 — Section 27.

---

## 📊 Batch Processing

- **Trigger:** Manual
- **Scope:** All rows in each source
- **Frequency:** Per run
- **Latency:** High (batch mode)

**Reference:** Unit 10 — Section 19.

---

## 🔗 Related Documents

- [`data_dictionary.md`](data_dictionary.md)
- [`schema.md`](schema.md)
- [`validation_rules.md`](validation_rules.md)
- [`../README.md`](../README.md)

---

## 📌 Notes

- All timestamps use UTC (ISO 8601).
- Logs → `logs/pipeline.log` + console.
- Pipeline restartable.
- MongoDB + Scraper optional.
- Follows Unit 7, 8, 10, 11 specifications.