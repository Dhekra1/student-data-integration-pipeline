# Validation Rules

This document defines all validation rules applied to the student dataset inside the pipeline. Each rule is enforced in `src/validate.py` and tested in `tests/test_validation.py`.

**Validation Layer:** Schema + Business
**Implementation:** `src/validate.py` → `validate_students()`
**Execution:** After transformation, before loading to the database
**Failure Behavior:** Raises `ValueError` (pipeline stops) OR rejects the row (quarantine)

---

## 📌 Validation Philosophy

The pipeline follows a **fail-fast** approach for schema violations, and a **quarantine** approach for recoverable row-level errors:

- If a **critical rule** fails (missing columns, empty dataset) → pipeline stops.
- If a **row-level issue** is found (invalid age, malformed email) → the row is moved to `data/rejected/` and processing continues.

All validation failures are logged with detailed context.

**Reference:** Unit 10 — Sections 27, 29–31.

---

## ✅ Rules Overview

| # | Rule | Field | Level | Action |
|---|------|-------|-------|--------|
| 1 | Required columns present | All | Schema | Fail |
| 2 | Dataset is not empty | — | Schema | Fail |
| 3 | `student_id` is unique | `student_id` | Business | Fail |
| 4 | `student_id` is not null | `student_id` | Schema | Fail |
| 5 | `name` is not null | `name` | Schema | Fail |
| 6 | `age` is between 16 and 80 | `age` | Business | Fail |
| 7 | `gpa` is between 0.0 and 4.0 | `gpa` | Business | Fail |
| 8 | `attendance` is between 0 and 100 | `attendance` | Business | Fail |

---

## 🔍 Rule Details

### Rule 1 — Required Columns Present

**Level:** Schema
**Field:** All
**Purpose:** Ensure the dataset contains every expected column.

**Expected columns:**

```python
REQUIRED_COLUMNS = ["student_id", "name", "age", "gpa", "attendance"]
```

**Implementation:**

```python
missing = set(REQUIRED_COLUMNS) - set(df.columns)
if missing:
    raise ValueError(f"Missing columns: {missing}")
```

**Why:** Downstream steps rely on these columns; missing ones cause cryptic errors later.

---

### Rule 2 — Dataset Is Not Empty

**Level:** Schema
**Field:** —
**Purpose:** Reject empty datasets early.

**Implementation:**

```python
if df.empty:
    raise ValueError("Dataset is empty.")
```

**Why:** An empty dataset usually indicates an upstream problem (empty file, wrong filter).

---

### Rule 3 — `student_id` Is Unique

**Level:** Business
**Field:** `student_id`
**Purpose:** Prevent duplicate student records.

**Implementation:**

```python
if not df["student_id"].is_unique:
    raise ValueError("student_id must be unique.")
```

**Why:** `student_id` is the **Primary Key**. Duplicates break joins and cause silent data corruption.

**Handling in Transform:** Duplicates are removed earlier by:

```python
df = df.drop_duplicates(subset=["student_id"], keep="first")
```

---

### Rule 4 — `student_id` Is Not Null

**Level:** Schema
**Field:** `student_id`
**Purpose:** Every record must have an identifier.

**Implementation:**

```python
if df["student_id"].isnull().any():
    raise ValueError("student_id contains null values.")
```

**Why:** A record without a key cannot be referenced or updated.

---

### Rule 5 — `name` Is Not Null

**Level:** Schema
**Field:** `name`
**Purpose:** Every record must have a student name.

**Implementation:**

```python
if df["name"].isnull().any():
    raise ValueError("name contains null values.")
```

**Why:** Used for reporting and identification.

---

### Rule 6 — `age` Is Between 16 and 80

**Level:** Business
**Field:** `age`
**Purpose:** Restrict ages to a valid range.

**Rule:** `16 ≤ age ≤ 80`

**Implementation:**

```python
if not df["age"].between(16, 80).all():
    raise ValueError("Age validation failed. Expected 16-80.")
```

**Why:** Students under 16 are not eligible; ages above 80 are likely data entry errors.

**Handling in Transform:** Invalid values are set to `NA` and imputed with the median:

```python
df.loc[~df["age"].between(16, 80), "age"] = pd.NA
df["age"] = df["age"].fillna(df["age"].median())
```

---

### Rule 7 — `gpa` Is Between 0.0 and 4.0

**Level:** Business
**Field:** `gpa`
**Purpose:** Restrict GPA to the standard 4.0 scale.

**Rule:** `0.0 ≤ gpa ≤ 4.0`

**Implementation:**

```python
if not df["gpa"].between(0, 4).all():
    raise ValueError("GPA validation failed. Expected 0-4.")
```

**Why:** Values outside this range indicate data errors.

**Handling in Transform:** Same as Rule 6.

---

### Rule 8 — `attendance` Is Between 0 and 100

**Level:** Business
**Field:** `attendance`
**Purpose:** Restrict attendance to a valid percentage.

**Rule:** `0 ≤ attendance ≤ 100`

**Implementation:**

```python
if not df["attendance"].between(0, 100).all():
    raise ValueError("Attendance validation failed. Expected 0-100.")
```

**Why:** Attendance is a percentage; values outside `[0, 100]` are invalid.

**Handling in Transform:** Same as Rule 6.

---

## 📄 CSV-Specific Rules (Row-Level Validation)

The following rules are applied **row-by-row** to raw CSV data in
`src/validate.py`. Rows with any error are saved to
`data/rejected/rejected_records.csv` with a semicolon-separated `errors` column.

| Field | Rule | Error Message |
|-------|------|---------------|
| `student_id` | Must be present | `student_id is required` |
| `student_id` | Duplicate detection | `duplicate student_id` |
| `name` | Must be present | `name is required` |
| `age` | Must be present, numeric | `age is required`, `age must be an integer` |
| `age` | Range 16–80 | `age must be between 16 and 80` |
| `email` | Must be present | `email is required` |
| `email` | Must match `^[^@]+@[^@]+\.[^@]+$` | `email format is invalid` |
| `phone` | Must be present, digits only | `phone is required`, `phone must contain only digits` |
| `phone` | Length 9–15 | `phone must contain between 9 and 15 digits` |

**Quarantine Layer:** Rejected rows are preserved for debugging and reprocessing (Unit 10 — Section 32).

---

## 🍃 MongoDB Validation (Unit 8)

MongoDB is more flexible than traditional relational models, but this does **not** mean data should be stored without rules.

**Reference:** Unit 8 — pages 47-49, 69.

### Connectivity Check

| Check | Implementation |
|-------|----------------|
| MongoDB reachable | `client.admin.command("ping")` |
| Collection accessible | `collection.count_documents({})` |

If connection fails, the pipeline logs the error and continues (MongoDB is optional).

---

### Document-Level Validation

| Check | Description | Implementation |
|-------|-------------|----------------|
| `student_id` exists | Every document must have an ID | Enforced by unique index |
| `student_id` unique per `(student_id, course_id)` | No duplicate pairs | Compound unique index |
| `name` exists | Not null | Application-level check |
| `gpa` range | 0.0 ≤ gpa ≤ 4.0 | Application-level check |
| `attendance` range | 0 ≤ attendance ≤ 100 | Application-level check |
| `age` range | 16 ≤ age ≤ 80 | Application-level check |

---

### Unique Index (Unit 8 — pages 49-50)

The pipeline creates a **compound unique index** on `(student_id, course_id)`:

```python
collection.create_index(
    [("student_id", ASCENDING), ("course_id", ASCENDING)],
    unique=True,
    name="uniq_student_course",
)
```

**Why:**
- Prevents duplicate enrollments.
- Enables idempotent `upsert` (Unit 8 — pages 35-36).
- Ensures each `(student, course)` pair appears at most once.

---

### Retrieval Validation

After loading, the pipeline verifies:

```python
total = count_documents(...)  # must equal number of rows loaded
```

If the count does not match, a warning is logged.

**Reference:** Unit 8 — page 69.

---

### Optional: JSON Schema Validation (Advanced)

For production, MongoDB supports JSON Schema validation (Unit 8 — pages 47-49):

```javascript
db.createCollection("validated_students", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["student_id", "name", "academic"],
      properties: {
        student_id: { bsonType: "int" },
        name: { bsonType: "string" },
        academic: {
          bsonType: "object",
          required: ["gpa"],
          properties: {
            gpa: { bsonType: "double", minimum: 0, maximum: 4 }
          }
        }
      }
    }
  }
})
```

**Note:** Not enforced in the current training pipeline; left as a future improvement.

---

## 🧪 Recoverable vs. Fatal Errors

Inspired by Unit 10 — Section 32:

| Type | Example | Action |
|------|---------|--------|
| **Recoverable** | One malformed record | Quarantine to `data/rejected/` and continue |
| **Fatal** | Missing required file, empty dataset | Log + raise + stop pipeline |
| **Optional MongoDB failure** | Connection refused | Log + continue (pipeline not stopped) |

**Current implementation:**

- **Row-level errors** → quarantine (`data/rejected/`)
- **Schema errors** → fatal (raise `ValueError`)
- **MongoDB errors** → logged only (pipeline continues)

---

## 🗂️ Validation Layers Diagram

```text
┌──────────────────────────────────────┐
│            Raw Data                  │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│         Transform Layer              │
│  - Deduplicate                       │
│  - Convert types                     │
│  - Apply business rules              │
│  - Impute missing values             │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│         Validate Layer               │
│                                      │
│  ┌────────────────────────────────┐  │
│  │  Schema Validation             │  │
│  │  - Required columns            │  │
│  │  - Non-empty dataset           │  │
│  │  - Non-null key fields         │  │
│  └────────────────────────────────┘  │
│                                      │
│  ┌────────────────────────────────┐  │
│  │  Business Validation           │  │
│  │  - Unique student_id           │  │
│  │  - Age range (16–80)           │  │
│  │  - GPA range (0.0–4.0)         │  │
│  │  - Attendance (0–100)          │  │
│  └────────────────────────────────┘  │
└──────────────┬───────────────────────┘
               │
               ▼
        ✅ Valid Data → Load
               │
               ├──────────────────────┐
               ▼                      ▼
        SQLite Table              MongoDB Collection
        `students`                `students`
        (schema checks)           (unique index +
                                  application checks)
```

---

## 📊 Validation Report (Future)

Future versions will generate a CSV report at `reports/quality_report.csv` with:

| Column | Description |
|--------|-------------|
| `batch_id` | Pipeline run identifier |
| `total_rows` | Total records in dataset |
| `passed_rows` | Records that passed all rules |
| `failed_rows` | Records that failed at least one rule |
| `rule` | Name of the failed rule |
| `failed_count` | How many rows failed this rule |
| `timestamp` | When the validation ran |

---

## 🧩 Mapping Rules to Code

| Rule | File | Function |
|------|------|----------|
| Required columns | `src/validate.py` | `validate_students` |
| Non-empty dataset | `src/validate.py` | `validate_students` |
| Unique `student_id` | `src/validate.py` | `validate_students` |
| Null checks | `src/validate.py` | `validate_students` |
| Age range | `src/validate.py` | `validate_students` |
| GPA range | `src/validate.py` | `validate_students` |
| Attendance range | `src/validate.py` | `validate_students` |
| Row-level CSV rules | `src/validate.py` | `validate_csv_data` |
| **MongoDB connection** | `src/mongo_loader.py` | `get_mongo_client` |
| **MongoDB unique index** | `src/mongo_loader.py` | `create_indexes` |
| **MongoDB count check** | `src/mongo_loader.py` | `count_documents` |

---

## 🔗 Related Documents

- [`data_dictionary.md`](data_dictionary.md) — Field definitions
- [`schema.md`](schema.md) — Database schema (SQLite + MongoDB)
- [`pipeline.md`](pipeline.md) — Pipeline stages
- [`../README.md`](../README.md) — Project overview

---

## 📌 Notes

- **All schema rules are fatal.** Row-level CSV rules quarantine the offending rows.
- **MongoDB failures are non-fatal** — the pipeline continues.
- Rules are enforced in `src/validate.py` and `src/mongo_loader.py`.
- Update this document whenever a new rule is added or changed.
- Documentation follows **Unit 8 — Sections 47-51**, **Unit 10 — Sections 29–31**, and **Unit 11 — Section 42**.