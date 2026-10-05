# Database Schema

This document describes the structure of the databases used by the AI Data Engineering Pipeline — including **SQLite** (relational) and **MongoDB** (semi-structured).

**Relational Engine:** SQLite
**Relational File:** `data/processed/students.db`
**Document Engine:** MongoDB 7.0
**Document Database:** `university_ai`
**Schema Version:** 1.1
**Last Updated:** 2026-10-05

---

## 📋 Tables & Collections Overview

| Storage | Name | Description | Populated By |
|---------|------|-------------|--------------|
| SQLite | `students` | Final integrated ML-ready dataset | `src/load.py` |
| SQLite | `courses` | Course catalog (seed data) | `src/extract.py` |
| SQLite | `enrollments` | Student-course associations (seed data) | `src/extract.py` |
| MongoDB | `students` | Semi-structured mirror of final dataset | `src/mongo_loader.py` |

---

# Part 1 — SQLite Schema

## 🗂️ Table: `students`

### Purpose

The **final output** of the pipeline. It is a denormalized dataset created
from the CSV + API + SQLite integration, cleaned and validated.

### Definition

```sql
CREATE TABLE students (
    student_id    INTEGER PRIMARY KEY,
    name          TEXT    NOT NULL,
    age           INTEGER NOT NULL CHECK (age BETWEEN 16 AND 80),
    email         TEXT,
    phone         TEXT,
    attendance    REAL    CHECK (attendance BETWEEN 0 AND 100),
    gpa           REAL    CHECK (gpa BETWEEN 0.0 AND 4.0),
    status        TEXT,
    course_id     INTEGER,
    course_name   TEXT,
    credit_hours  INTEGER,
    semester      TEXT,
    score         REAL,
    source        TEXT,
    source_url    TEXT,
    retrieved_at  TEXT
);
```

### Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `student_id` | INTEGER | ❌ No | **Primary Key.** Unique student identifier |
| `name` | TEXT | ❌ No | Full name of the student |
| `age` | INTEGER | ❌ No | Age in years (16–80) |
| `email` | TEXT | ✅ Yes | Email address |
| `phone` | TEXT | ✅ Yes | Contact phone number |
| `attendance` | REAL | ✅ Yes | Attendance percentage (0–100) |
| `gpa` | REAL | ✅ Yes | Grade Point Average (0.0–4.0) |
| `status` | TEXT | ✅ Yes | Enrollment status (`Active` / `Inactive`) |
| `course_id` | INTEGER | ✅ Yes | Course identifier |
| `course_name` | TEXT | ✅ Yes | Course name |
| `credit_hours` | INTEGER | ✅ Yes | Credit hours |
| `semester` | TEXT | ✅ Yes | Semester label (e.g., `2026-1`) |
| `score` | REAL | ✅ Yes | Course score |
| `source` | TEXT | ✅ Yes | **Provenance.** Source label |
| `source_url` | TEXT | ✅ Yes | **Provenance.** Source URL or path |
| `retrieved_at` | TEXT | ✅ Yes | **Provenance.** UTC timestamp (ISO 8601) |

### Keys & Constraints

| Constraint | Column | Rule |
|------------|--------|------|
| **Primary Key** | `student_id` | Uniquely identifies each student |
| `NOT NULL` | `name` | Student must have a name |
| `NOT NULL` | `age` | Age is mandatory |
| `CHECK` | `age` | 16 ≤ age ≤ 80 |
| `CHECK` | `gpa` | 0.0 ≤ gpa ≤ 4.0 |
| `CHECK` | `attendance` | 0 ≤ attendance ≤ 100 |

### Notes

- `student_id` is unique in the source, but a student may appear on multiple
  rows in the **final dataset** if they have multiple course enrollments.
- `source`, `source_url`, `retrieved_at` are added by `add_provenance()`
  (Unit 7 — pages 77–78).

---

## 🗂️ Table: `courses`

### Purpose

A seed catalog of courses used by the pipeline to simulate a relational
external source.

### Definition

```sql
CREATE TABLE courses (
    course_id    INTEGER PRIMARY KEY,
    course_name  TEXT    NOT NULL,
    credit_hours INTEGER
);
```

### Seed Data

| course_id | course_name | credit_hours |
|-----------|-------------|--------------|
| 1 | Python Programming | 3 |
| 2 | Database Systems | 3 |
| 3 | Artificial Intelligence | 4 |

---

## 🗂️ Table: `enrollments`

### Purpose

Associates students with courses. Used to demonstrate multi-source integration.

### Definition

```sql
CREATE TABLE enrollments (
    student_id  INTEGER,
    course_id   INTEGER,
    semester    TEXT,
    score       REAL
);
```

### Columns

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `student_id` | INTEGER | ❌ No | Student identifier |
| `course_id` | INTEGER | ❌ No | Course identifier |
| `semester` | TEXT | ✅ Yes | Semester label (e.g., `2026-1`) |
| `score` | REAL | ✅ Yes | Score achieved |

### Relationships

| Relationship | Type | Description |
|--------------|------|-------------|
| `enrollments.student_id` → `students.student_id` | Many-to-One | A student may have many enrollments |
| `enrollments.course_id` → `courses.course_id` | Many-to-One | A course may have many enrollments |

> ⚠️ SQLite does not enforce foreign keys by default. The extraction query
> performs a JOIN on `course_id`.

### Seed Data

| student_id | course_id | semester | score |
|------------|-----------|----------|-------|
| 1001 | 1 | 2026-1 | 88.0 |
| 1001 | 2 | 2026-1 | 91.0 |
| 1002 | 1 | 2026-1 | 95.0 |
| 1002 | 3 | 2026-1 | 89.0 |
| 1003 | 2 | 2026-1 | 72.0 |
| 1004 | 1 | 2026-1 | 84.0 |

---

## 🔗 SQLite Relationships Diagram

```text
┌──────────────┐         ┌──────────────────┐         ┌──────────────┐
│   students   │         │   enrollments    │         │   courses    │
├──────────────┤         ├──────────────────┤         ├──────────────┤
│ student_id PK│◄────────┤ student_id       │         │ course_id PK │
│ name         │  1   N  │ course_id        ├────────►│ course_name  │
│ age          │         │ semester         │   N   1 │ credit_hours │
│ email        │         │ score            │         └──────────────┘
│ phone        │         └──────────────────┘
│ attendance   │
│ gpa          │
│ status       │
│ course_id    │
│ course_name  │
│ credit_hours │
│ semester     │
│ score        │
│ source       │
│ source_url   │
│ retrieved_at │
└──────────────┘
```

---

# Part 2 — MongoDB Schema

## 🍃 Collection: `students`

### Purpose

A **semi-structured mirror** of the final dataset. Enables:
- Aggregation Pipeline analytics.
- Flexible schema evolution.
- Nested documents (future).
- Array-based features (future).

### Database

- **Name:** `university_ai`
- **Connection:** `mongodb://localhost:27017/`

### Document Structure

```javascript
{
  _id: ObjectId("..."),                     // MongoDB auto-generated
  student_id: 1001,                         // Integration key
  name: "Ahmed Ali",
  age: 21,
  email: "ahmed@example.com",
  phone: 777123456,
  attendance: 92.0,
  gpa: 3.45,
  status: "Active",
  course_id: 1,
  course_name: "Python Programming",
  credit_hours: 3,
  semester: "2026-1",
  score: 88.0,
  source: "csv+api+database",               // Provenance
  source_url: "multi-source",               // Provenance
  retrieved_at: "2026-10-05T12:55:33+00:00" // Provenance
}
```

### Fields

Same fields as the SQLite `students` table (see Part 1).

### Index

| Index Name | Fields | Type | Purpose |
|------------|--------|------|---------|
| `uniq_student_course` | `(student_id, course_id)` | **Unique** | Idempotent upsert (Unit 8 — pages 49-50) |

### Idempotency Strategy

The pipeline uses `update_one(..., upsert=True)` keyed on
`(student_id, course_id)`. Re-running the pipeline will **update existing
documents** instead of creating duplicates.

**Reference:** Unit 8 — pages 35-36.

### Sample Queries

```javascript
// Find all students in a specific course
db.students.find({ course_id: 1 })

// Find students with GPA >= 3.5
db.students.find({ gpa: { $gte: 3.5 } })

// Find students by status
db.students.find({ status: "Active" })

// Count documents per status (Aggregation)
db.students.aggregate([
  { $group: { _id: "$status", count: { $sum: 1 } } }
])

// Average GPA per status (Aggregation)
db.students.aggregate([
  { $group: { _id: "$status", avg_gpa: { $avg: "$gpa" } } }
])

// Sort by GPA descending
db.students.find().sort({ gpa: -1 })

// Projection — return only selected fields
db.students.find({}, { student_id: 1, name: 1, gpa: 1, _id: 0 })
```

**Reference:** Unit 8 — pages 15-17, 50-51.

---

## 🍃 SQLite vs. MongoDB — Design Rationale

| Aspect | SQLite | MongoDB |
|--------|:---:|:---:|
| **Purpose** | Structured final dataset | Semi-structured mirror |
| **Schema** | Fixed (with constraints) | Flexible |
| **Primary Use** | Joins, transactions | Aggregation, nesting |
| **Idempotency** | Table replace | Upsert with index |
| **Relationships** | Foreign keys (logical) | Embedded / referenced |
| **Analytics** | SQL | Aggregation Pipeline |

**Both storages coexist** — they serve different purposes (Unit 8 — page 52).

---

## 🔄 Idempotency Strategy (Both Engines)

To ensure **safe re-runs** (Unit 10 — Section 23):

| Storage | Strategy |
|---------|----------|
| **SQLite** | `df.to_sql(..., if_exists="replace")` |
| **MongoDB** | `update_one(..., upsert=True)` with unique `(student_id, course_id)` index |
| **Future (PostgreSQL)** | `INSERT ... ON CONFLICT (student_id) DO UPDATE` |

### Future Example (PostgreSQL)

```sql
INSERT INTO students (student_id, name, age, ...)
VALUES (1001, 'Ahmed Ali', 22, ...)
ON CONFLICT (student_id)
DO UPDATE SET
    name = EXCLUDED.name,
    age = EXCLUDED.age,
    gpa = EXCLUDED.gpa,
    attendance = EXCLUDED.attendance;
```

---

## 📊 Sample SQL Queries

### All students

```sql
SELECT * FROM students;
```

### Top 5 by GPA

```sql
SELECT student_id, name, gpa
FROM students
ORDER BY gpa DESC
LIMIT 5;
```

### Students by status

```sql
SELECT status, COUNT(*) AS count
FROM students
GROUP BY status;
```

### Average GPA per course

```sql
SELECT course_name, AVG(gpa) AS avg_gpa
FROM students
WHERE course_name IS NOT NULL
GROUP BY course_name;
```

### Data provenance audit

```sql
SELECT source, source_url, COUNT(*) AS rows
FROM students
GROUP BY source, source_url;
```

### Enrollment report

```sql
SELECT s.name, c.course_name, e.semester, e.score
FROM enrollments e
JOIN courses c ON e.course_id = c.course_id
JOIN students s ON e.student_id = s.student_id
ORDER BY s.name, c.course_name;
```

---

## 🔐 Data Types Reference

### SQLite

| SQLite Type | Python Equivalent | Example |
|-------------|-------------------|---------|
| INTEGER | `int` | `1001` |
| TEXT | `str` | `Ahmed Ali` |
| REAL | `float` | `3.45` |
| BLOB | `bytes` | (unused) |
| NULL | `None` | (missing) |

### MongoDB (BSON)

| BSON Type | Python Equivalent | Example |
|-----------|-------------------|---------|
| Int32 / Int64 | `int` | `1001` |
| String | `str` | `Ahmed Ali` |
| Double | `float` | `3.45` |
| Boolean | `bool` | `True` |
| ObjectId | `bson.ObjectId` | `ObjectId("...")` |
| Null | `None` | `null` |
| Array | `list` | `["Python", "SQL"]` |
| Document | `dict` | `{...}` |

**Reference:** Unit 8 — page 9 (BSON).

---

## 🧪 Testing Both Engines

Verify the SQLite database exists and has data:

```python
import sqlite3

conn = sqlite3.connect("data/processed/students.db")
tables = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()
print("Tables:", tables)

for table in ["students", "courses", "enrollments"]:
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"{table}: {count} rows")

conn.close()
```

Verify the MongoDB collection exists and has data:

```python
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
collection = client["university_ai"]["students"]

print("Total documents:", collection.count_documents({}))
print("Unique students:", len(collection.distinct("student_id")))
print("Indexes:", list(collection.list_indexes()))

client.close()
```

---

## 🔗 Related Documents

- [`data_dictionary.md`](data_dictionary.md) — Field definitions
- [`pipeline.md`](pipeline.md) — Pipeline stages
- [`validation_rules.md`](validation_rules.md) — Validation rules
- [`../README.md`](../README.md) — Project overview

---

## 📌 Notes

- **Training mode:** Uses SQLite + MongoDB for learning purposes.
- **Production mode (future):** Migrate to PostgreSQL (primary) + MongoDB (secondary).
- **Schema versioning:** Update the version at the top whenever the schema changes.
- Documentation follows **Unit 8 — Sections 8-14, 47-52** and **Unit 11 — Section 40**.