# AI Data Engineering Pipeline

An end-to-end data engineering pipeline that collects raw data from multiple sources (CSV, REST API, SQLite, and Web Scraping), preserves it, cleans and transforms it, validates data quality, and produces an ML-ready dataset stored in both SQLite and MongoDB.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Objectives](#objectives)
3. [Architecture](#architecture)
4. [Data Sources](#data-sources)
5. [Technologies](#technologies)
6. [Project Structure](#project-structure)
7. [Installation](#installation)
8. [Configuration](#configuration)
9. [Usage](#usage)
10. [Pipeline Steps](#pipeline-steps)
11. [Data Validation](#data-validation)
12. [Database Schema](#database-schema)
13. [MongoDB Storage](#mongodb-storage)
14. [Web Scraping](#web-scraping)
15. [Output](#output)
16. [Testing](#testing)
17. [Reproducibility](#reproducibility)
18. [Security & Privacy](#security--privacy)
19. [Data Provenance](#data-provenance)
20. [Limitations](#limitations)
21. [Future Improvements](#future-improvements)
22. [Documentation](#documentation)
23. [Author](#author)

---

## 📖 Overview

This project implements a complete ETL pipeline for processing student data from four sources. It follows professional data engineering practices:

- Extract data from CSV, REST API, SQLite, and HTML (Web Scraping).
- Preserve the raw data before any transformation.
- Clean, normalize, and integrate data from multiple sources.
- Validate data quality and business rules.
- Store the final result in a structured SQLite database.
- Store semi-structured data in MongoDB for aggregation and flexibility.
- Scrape supplementary data from HTML tables (Unit 7).
- Produce an ML-ready output for downstream analysis.
- Support re-runs without silently losing source data.

Built using Python with Pandas, Requests, BeautifulSoup, Flask, SQLAlchemy, PyMongo, and Python-dotenv.

---

## 🎯 Objectives

- Collect student data from CSV, API, SQLite, and Web sources.
- Preserve an original copy of the raw data.
- Clean and transform the dataset using standard ETL rules.
- Validate schema and data quality requirements.
- Integrate source data using a common key (`student_id`).
- Load the final dataset into SQLite.
- Load the final dataset into MongoDB (optional, when enabled).
- Scrape HTML tables responsibly (Unit 7).
- Generate a reproducible project workflow with documentation and tests.

---

## 🏗️ Architecture

```text
SOURCE (CSV + API + SQLite)
   ↓
EXTRACT
   ↓
RAW COPY (Preserved)
   ↓
TRANSFORM (Clean + Standardize)
   ↓
VALIDATE (Schema + Business Rules)
   ↓
LOAD (SQLite + MongoDB)
   ↓
ML-READY DATASET

+ Web Scraping (Unit 7) → data/processed/web_students.csv
```

Each stage is implemented as a separate module in `src/`.

---

## 🌐 Data Sources

| Property | Value |
|----------|-------|
| **Source Name** | Student Data (Training) |
| **Source Types** | CSV, REST API, SQLite, HTML |
| **CSV File** | `data/raw/students.csv` |
| **Mock API** | `http://127.0.0.1:5000/students` |
| **SQLite Database** | `data/processed/students.db` |
| **Web HTML File** | `data/raw/web_students.html` |
| **MongoDB URI** | `mongodb://localhost:27017/` |
| **Update Frequency** | Manual / batch-based |
| **Purpose** | Training and ETL demonstration |
| **License** | Educational use only |

### Data Acquisition (Unit 7)

- **API**: REST endpoint served by a local Flask mock.
- **CSV**: Local file snapshot of student records.
- **SQLite**: Relational source for courses and enrollments.
- **HTML**: Local mock web page for scraping practice.

Raw copies preserved in:

- `data/raw/students_raw_backup.csv` — CSV snapshot
- `data/raw/api_response.json` — Raw API JSON response
- `data/staging/extracted_students.csv` — Staging copy

---

## 🛠️ Technologies

- Python 3.10+
- Pandas 2.2
- Requests 2.31
- BeautifulSoup 4.12 (Web Scraping)
- lxml 5.1 (HTML parser)
- Flask 3.1 (Mock API)
- SQLAlchemy 2.0
- SQLite
- MongoDB 7.0 (semi-structured storage)
- PyMongo 4.6 (Python MongoDB driver)
- Python-dotenv
- Pytest

---

## 📁 Project Structure

```text
student_data_integration_pipeline/
│
├── config/
│   └── config.example.json
│
├── data/
│   ├── raw/
│   │   ├── students.csv
│   │   ├── students_raw_backup.csv
│   │   ├── api_response.json
│   │   └── web_students.html
│   ├── staging/
│   │   └── extracted_students.csv
│   ├── processed/
│   │   ├── final_dataset.csv
│   │   ├── valid_students.csv
│   │   ├── web_students.csv
│   │   └── students.db
│   └── rejected/
│       └── rejected_records.csv
│
├── docs/
│   ├── data_dictionary.md
│   ├── pipeline.md
│   ├── schema.md
│   └── validation_rules.md
│
├── logs/
│   └── pipeline.log
│
├── reports/
│   └── .gitkeep
│
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── extract.py
│   ├── load.py
│   ├── logging_config.py
│   ├── main.py
│   ├── mongo_loader.py       ← MongoDB layer (Unit 8)
│   ├── scraper.py            ← Web Scraping layer (Unit 7)
│   ├── transform.py
│   └── validate.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── mock_api.py
│   ├── test_api_source.py
│   ├── test_csv_source.py
│   ├── test_database_source.py
│   ├── test_mongo.py          ← MongoDB tests
│   ├── test_output.py
│   ├── test_scraper.py        ← Web Scraping tests
│   ├── test_transform.py
│   └── test_validation.py
│
├── .env.example
├── .gitignore
├── main.py
├── README.md
└── requirements.txt
```

---

## 🚀 Installation

### 1. Clone

```bash
git clone https://github.com/Dhekra1/student_data_integration_pipeline.git
cd student_data_integration_pipeline
```

### 2. Virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # Linux / macOS
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. (Optional) Install and start MongoDB

- Install: https://www.mongodb.com/try/download/community
- Ensure service is running: `Get-Service -Name MongoDB`
- Set `MONGO_ENABLED=true` in `.env`.

---

## ⚙️ Configuration

Copy `.env.example` to `.env`:

```bash
copy .env.example .env       # Windows
cp .env.example .env         # Linux / macOS
```

> ⚠️ **Never commit `.env`.** It is excluded via `.gitignore`.

### MongoDB Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGO_URI` | `mongodb://localhost:27017/` | Connection string |
| `MONGO_DB_NAME` | `university_ai` | Target database |
| `MONGO_COLLECTION` | `students` | Target collection |
| `MONGO_TIMEOUT_MS` | `5000` | Server selection timeout |
| `MONGO_ENABLED` | `false` | Enable MongoDB load |

---

## ▶️ Usage

### Step 1 — Start the mock API (optional)

```bash
python tests/mock_api.py
```

Listens on `http://127.0.0.1:5000/students`.

### Step 2 — Run the pipeline

```bash
python main.py
```

Expected:

- Data extracted from all configured sources.
- Raw data preserved in `data/raw/`.
- Invalid records rejected into `data/rejected/`.
- Web data scraped from `data/raw/web_students.html`.
- Final output stored in `data/processed/`.
- MongoDB loaded (if enabled).
- Logs written to `logs/pipeline.log`.

---

## 🔄 Pipeline Steps

### 1. Extract
Reads from CSV, REST API, and SQLite.

### 2. Raw Storage
Preserves CSV snapshot, API JSON, and staging copy.

### 3. Transform
Deduplication, numeric conversion, business rules, imputation, integration, provenance tagging.

### 4. Validate
Schema + business rules (age 16–80, GPA 0–4, attendance 0–100, unique student_id).

### 5. Load to SQLite
Writes `final_dataset.csv`, `students.db`, `valid_students.csv`, `rejected_records.csv`.

### 6. Load to MongoDB (Optional)
Upserts into `university_ai.students` with compound unique index `(student_id, course_id)`.

### 7. Web Scraping
Reads `data/raw/web_students.html`, parses HTML with BeautifulSoup, saves to `data/processed/web_students.csv`.

**Reference:** Unit 7 — pages 45-63.

---

## ✅ Data Validation

| Rule | Description |
|------|-------------|
| Required columns | Expected fields present |
| Non-empty dataset | Rejects empty input |
| Unique `student_id` | No duplicates |
| Age range | 16 ≤ age ≤ 80 |
| GPA range | 0.0 ≤ gpa ≤ 4.0 |
| Attendance range | 0 ≤ attendance ≤ 100 |

For complete rules, see [`docs/validation_rules.md`](docs/validation_rules.md).

---

## 🗄️ Database Schema

SQLite table `students`:

| Column | Type | Constraint |
|--------|------|------------|
| `student_id` | INTEGER | Primary key |
| `name` | TEXT | Not null |
| `age` | INTEGER | 16–80 |
| `gpa` | REAL | 0.0–4.0 |
| `attendance` | REAL | 0–100 |

Additional tables: `courses`, `enrollments`.

See [`docs/schema.md`](docs/schema.md).

---

## 🍃 MongoDB Storage

- **Database:** `university_ai`
- **Collection:** `students`
- **Index:** Compound unique `(student_id, course_id)`

Each document mirrors a row from `final_dataset.csv`. Query examples in [`docs/schema.md`](docs/schema.md).

---

## 🕸️ Web Scraping

Reads HTML from `data/raw/web_students.html` (local mock), extracts a student table with BeautifulSoup, and saves to `data/processed/web_students.csv`.

Fields extracted:
- `student_id`, `name`, `city`, `gpa`, `skills`
- `source`, `source_url`, `retrieved_at` (provenance)

**Responsible Scraping** (Unit 7 — pages 53-55):
- Uses a descriptive User-Agent.
- Prefers APIs when available.
- Respects rate limits.
- Uses local HTML for training.

---

## 📤 Output

After a run:

- `data/raw/students_raw_backup.csv`
- `data/raw/api_response.json`
- `data/staging/extracted_students.csv`
- `data/processed/final_dataset.csv`
- `data/processed/valid_students.csv`
- `data/processed/web_students.csv`
- `data/processed/students.db`
- MongoDB collection `university_ai.students` (optional)
- `data/rejected/rejected_records.csv`
- `logs/pipeline.log`

---

## 🧪 Testing

```bash
pytest tests/ -v
```

Coverage:

- API extraction
- CSV extraction
- Database extraction
- MongoDB integration (9 tests)
- Web Scraping (12 tests)
- Transformation
- Validation
- Output generation

**All tests pass (30/30).**

---

## 🔁 Reproducibility

1. Clone.
2. Virtual env.
3. Install dependencies.
4. Copy `.env.example` to `.env`.
5. (Optional) Start mock API.
6. (Optional) Ensure MongoDB is running.
7. Run `python main.py`.
8. Verify outputs.

---

## 🔒 Security & Privacy

- `.env` excluded from Git.
- No secrets in source code.
- Synthetic data only.
- Raw and rejected files preserved for traceability.
- MongoDB credentials via environment variables.
- Scraping follows ethical guidelines.

---

## 📍 Data Provenance

| Column | Description |
|--------|-------------|
| `source` | Source label (e.g., `csv+api+database`, `web_scraping`) |
| `source_url` | URL or path of the source |
| `retrieved_at` | UTC timestamp (ISO 8601) |

---

## ⚠️ Limitations

- Educational use only.
- SQLite not for high-concurrency production.
- MongoDB requires a local instance.
- Rule-based transformations.
- Mock API is local.
- Web scraping uses a local HTML file (not a real website).

---

## 🔮 Future Improvements

- ✅ MongoDB support (completed).
- ✅ Web Scraping (completed).
- PostgreSQL support.
- Nested documents + array queries.
- Orchestration (Airflow / Prefect).
- CI/CD (GitHub Actions).
- Data quality reports.

---

## 📚 Documentation

- [`docs/data_dictionary.md`](docs/data_dictionary.md)
- [`docs/schema.md`](docs/schema.md)
- [`docs/pipeline.md`](docs/pipeline.md)
- [`docs/validation_rules.md`](docs/validation_rules.md)

---

## 👤 Author

**Dhekra Al-Hussaini**

- GitHub: [@Dhekra1](https://github.com/Dhekra1)
- Email: dhekraalhusseini@gmail.com

---

## 📄 License

Educational purposes only.