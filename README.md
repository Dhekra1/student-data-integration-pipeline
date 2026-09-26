# Student Data Integration & ETL Pipeline

## 1. Project Overview

This project implements a Python-based Data Integration and ETL Pipeline for processing student data from multiple sources.

The pipeline extracts data from:

1. CSV file
2. REST API
3. SQLite database

The extracted data is validated, cleaned, integrated, transformed, validated again, and then saved as a final dataset.

The project also keeps rejected records and generates pipeline logs for monitoring and troubleshooting.

---

## 2. Project Architecture

The pipeline follows this general flow:

```text
CSV File ────────┐
                 │
REST API ────────┼──> Extract
                 │
SQLite Database ─┘
                      │
                      ▼
                  Validation
                      │
             ┌────────┴────────┐
             │                 │
          Valid Data      Rejected Data
             │                 │
             ▼                 ▼
        Transformation    rejected_records.csv
             │
             ▼
       Final Validation
             │
             ▼
      final_dataset.csv
             │
             ▼
       SQLite Load
```

---

## 3. Project Structure

```text
student_data_pipeline_db/
│
├── app/
│   ├── sources/
│   │   ├── csv_source.py
│   │   ├── api_source.py
│   │   └── database_source.py
│   │
│   ├── validation/
│   │   ├── student_validator.py
│   │   ├── validate_csv.py
│   │   └── final_validator.py
│   │
│   ├── output/
│   │   └── save_data.py
│   │
│   ├── utils/
│   │   └── logger.py
│   │
│   ├── extract.py
│   ├── transform.py
│   └── load.py
│
├── data/
│   ├── raw/
│   │   └── students.csv
│   │
│   ├── processed/
│   │   ├── valid_students.csv
│   │   └── final_dataset.csv
│   │
│   └── rejected/
│       └── rejected_records.csv
│
├── database/
│   └── students.db
│
├── logs/
│   └── pipeline.log
│
├── tests/
│   ├── conftest.py
│   ├── test_api_source.py
│   ├── test_csv_source.py
│   ├── test_database_source.py
│   ├── test_output.py
│   ├── test_transform.py
│   └── test_validation.py
│
├── create_database.py
├── mock_api.py
├── main.py
├── requirements.txt
└── README.md
```

---

## 4. Data Sources

### 4.1 CSV Source

The CSV source contains basic student information:

* Student ID
* Name
* Age
* Email
* Phone

The file is located at:

```text
data/raw/students.csv
```

The CSV data is extracted using Pandas.

---

### 4.2 REST API

The REST API provides additional student information:

* Student ID
* Attendance
* GPA
* Status

The project uses a local Mock API during development:

```text
http://127.0.0.1:5000/students
```

The API is accessed using the `requests` library.

---

### 4.3 SQLite Database

The SQLite database contains enrollment information and course details.

The database includes:

* Courses
* Enrollments

The database file is:

```text
database/students.db
```

The extracted information includes:

* Student ID
* Course ID
* Course name
* Credit hours
* Semester
* Score

---

## 5. ETL Pipeline

### 5.1 Extract

The Extract stage retrieves data from all three sources:

```text
CSV
REST API
SQLite
```

The extraction logic is located in:

```text
app/sources/
```

and coordinated by:

```text
app/extract.py
```

---

### 5.2 Validate

The CSV student records are validated before integration.

The validation checks include:

* Required student ID
* Required name
* Required age
* Valid age range
* Required email
* Valid email format
* Required phone number
* Valid phone format
* Duplicate student IDs

Invalid records are separated from valid records.

---

### 5.3 Clean

The pipeline performs data cleaning before producing the final dataset.

Examples include:

* Converting age values to integer values
* Cleaning text fields
* Removing duplicate student records
* Preserving missing values from sources where no matching record exists

---

### 5.4 Integrate

The data from the different sources is integrated using:

```text
student_id
```

The student information from the CSV is combined with:

* Attendance and GPA from the API
* Course and enrollment information from SQLite

A left join is used so that valid CSV students remain in the final dataset even when additional information is unavailable.

---

### 5.5 Transform

The transformation stage combines the extracted datasets into a unified Pandas DataFrame.

The transformation also performs:

* Numeric type normalization
* Text cleanup
* Source integration
* Final dataset preparation

The main transformation module is:

```text
app/transform.py
```

---

### 5.6 Final Validation

After transformation, the final dataset is validated again.

The final validation checks:

* Required columns
* Missing student IDs
* Missing names
* Missing ages
* Invalid age values

Only after successful final validation is the final dataset saved.

---

### 5.7 Load

The final transformed dataset is loaded into the SQLite database.

The destination table is:

```text
final_students
```

The loading logic is implemented in:

```text
app/load.py
```

---

## 6. Data Quality Handling

The pipeline demonstrates several data quality rules.

### Missing Values

Records with required missing values are rejected during validation.

For example:

```text
Student 1006
Age = missing
```

is rejected.

### Invalid Values

Values outside the accepted range are rejected.

For example:

```text
Student 1007
Age = 150
```

is rejected because the accepted age range is 16–100.

### Duplicate Records

Duplicate student IDs are detected and rejected.

For example:

```text
Student 1008
```

appears twice in the raw CSV data.

Only the first valid occurrence is retained.

---

## 7. Rejected Records

Rejected records are saved separately so that invalid data is not silently lost.

The output file is:

```text
data/rejected/rejected_records.csv
```

The file contains the original student information and the reason for rejection.

Examples of rejection reasons include:

```text
age is required
age must be between 16 and 100
duplicate student_id
```

---

## 8. Final Output

The main processed output is:

```text
data/processed/final_dataset.csv
```

The dataset combines information from the three sources.

The pipeline currently produces 8 final rows because some students have multiple course records.

For example, a student may appear more than once when enrolled in multiple courses.

---

## 9. Logging

Pipeline execution is recorded in:

```text
logs/pipeline.log
```

The log records important pipeline stages such as:

* Pipeline started
* Extraction completed
* Validation completed
* Transformation completed
* Final validation completed
* Final dataset saved
* Database load completed
* Pipeline completed

Logging is implemented using Python's built-in `logging` module.

---

## 10. Installation

Install the required Python packages using:

```bash
pip install -r requirements.txt
```

The project uses:

* Python
* Pandas
* Requests
* Flask
* Pytest
* SQLite

---

## 11. Running the Project

### Step 1: Start the Mock API

Start the local API defined in:

```text
mock_api.py
```

The API should be available at:

```text
http://127.0.0.1:5000/students
```

### Step 2: Run the Pipeline

From the project root:

```bash
python main.py
```

The pipeline will:

```text
Extract
→ Validate
→ Save validation results
→ Transform
→ Final Validate
→ Save final dataset
→ Load into SQLite
```

---

## 12. Running Tests

The project uses `pytest`.

Run all tests using:

```bash
pytest
```

The test suite covers:

* CSV extraction
* REST API extraction
* SQLite extraction
* Duplicate handling
* Invalid record rejection
* Source integration
* Final dataset creation
* Rejected records creation

All current tests pass successfully.

---

## 13. Output Files

### Valid Intermediate Data

```text
data/processed/valid_students.csv
```

Contains student records that passed the initial validation.

### Final Dataset

```text
data/processed/final_dataset.csv
```

Contains the integrated and transformed dataset.

### Rejected Records

```text
data/rejected/rejected_records.csv
```

Contains records rejected during validation and their rejection reasons.

### Pipeline Log

```text
logs/pipeline.log
```

Contains execution logs.

---

## 14. Why Use a Data Pipeline?

A data pipeline provides a structured and repeatable way to collect, validate, transform, integrate, and load data.

Without a pipeline, data processing may require manual operations that are difficult to reproduce and monitor.

The pipeline also separates responsibilities into different stages, making the system easier to maintain and test.

---

## 15. Raw Data vs Processed Data

### Raw Data

Raw data is the original data extracted from its source.

Examples:

```text
students.csv
REST API response
SQLite records
```

Raw data should generally remain unchanged so that the original source information can be traced.

### Processed Data

Processed data has been validated, cleaned, integrated, and transformed into a form suitable for analysis or further processing.

In this project:

```text
final_dataset.csv
```

represents the processed output.

---

## 16. ETL vs Data Integration

ETL stands for:

```text
Extract
Transform
Load
```

Data integration focuses on combining data from different sources into a unified view.

This project performs both:

```text
Extract data from multiple sources
→ Validate and clean
→ Integrate the sources
→ Transform the data
→ Load the result
```

---

## 17. Handling Missing Values

Missing values should be handled according to the meaning and importance of each field.

In this project, required student information such as age is validated and invalid records are rejected.

For optional information coming from the API or SQLite database, missing values can remain as missing when no matching record exists.

---

## 18. Why Remove Duplicates?

Duplicates can cause:

* Incorrect record counts
* Repeated information
* Incorrect analysis
* Inconsistent results

The pipeline detects duplicate student IDs during validation.

However, multiple rows for the same student can still be valid in the final dataset when they represent different course enrollments.

---

## 19. Why Separate Extraction and Transformation?

Separating extraction from transformation improves maintainability.

Extraction is responsible for obtaining data from sources.

Transformation is responsible for cleaning, combining, and preparing the data.

This separation makes individual components easier to:

* Test
* Modify
* Reuse
* Debug

---

## 20. Why Is Validation Important?

Validation prevents invalid data from entering later stages of the pipeline.

It also makes data quality problems visible instead of silently producing incorrect results.

Rejected records are preserved with their rejection reasons so that data problems can be investigated.

---

## 21. Scheduling and Automation

A production pipeline can be scheduled using tools such as:

* Cron
* Windows Task Scheduler
* Apache Airflow
* Cloud workflow services

Scheduling allows the pipeline to run automatically at predefined intervals.

---

## 22. Scaling to Millions of Records

For very large datasets, the pipeline could be improved by using:

* Batch processing
* Database indexing
* Chunked file processing
* Distributed processing
* Cloud storage
* Data processing frameworks such as Spark

The current implementation is designed as a small educational ETL pipeline and is not intended for millions of records without further optimization.

---

## 23. Batch vs Streaming

### Batch Processing

Processes data periodically in groups.

Example:

```text
Run the pipeline once every day.
```

### Streaming

Processes data continuously or near real time.

Example:

```text
Process each incoming student event as it arrives.
```

The current project uses a batch-processing approach.

---

## 24. Conclusion

This project demonstrates a complete educational ETL workflow using Python.

The pipeline integrates data from:

```text
CSV
REST API
SQLite
```

and applies:

```text
Extraction
Validation
Cleaning
Integration
Transformation
Final Validation
Loading
Logging
Testing
```

The final result is a structured and validated student dataset that can be used for further analysis or downstream processing.
