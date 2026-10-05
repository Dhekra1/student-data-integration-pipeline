from pathlib import Path

from src.extract import extract_csv
from src.validate import validate_csv_data, validate_student_record


def test_duplicates_removed():

    data = extract_csv(Path("data/raw/students.csv"))

    valid_students, rejected_students = validate_csv_data(data)

    valid_ids = [
        student["student_id"]
        for student in valid_students
    ]

    assert len(valid_ids) == len(set(valid_ids))

    duplicate_errors = [
        item
        for item in rejected_students
        if "duplicate student_id" in item["errors"]
    ]

    assert len(duplicate_errors) > 0
    

def test_invalid_records_rejected():

    data = extract_csv(Path("data/raw/students.csv"))

    valid_students, rejected_students = validate_csv_data(data)

    rejected_ids = [
        item["student"]["student_id"]
        for item in rejected_students
    ]

    assert 1006 in rejected_ids
    assert 1007 in rejected_ids


def test_student_validation_accepts_a_valid_record():
    student = {
        "student_id": 2001,
        "name": "Test Student",
        "age": 21,
        "email": "test.student@example.com",
        "phone": "123456789",
    }

    assert validate_student_record(student) == []


def test_student_validation_rejects_an_out_of_range_age():
    student = {
        "student_id": 2002,
        "name": "Invalid Age",
        "age": 101,
        "email": "invalid.age@example.com",
        "phone": "123456789",
    }

    assert "age must be between 16 and 100" in validate_student_record(student)