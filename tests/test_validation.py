from app.validation.validate_csv import validate_csv_data
from app.sources.csv_source import extract_csv


def test_duplicates_removed():

    data = extract_csv("data/raw/students.csv")

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

    data = extract_csv("data/raw/students.csv")

    valid_students, rejected_students = validate_csv_data(data)

    rejected_ids = [
        item["student"]["student_id"]
        for item in rejected_students
    ]

    assert 1006 in rejected_ids
    assert 1007 in rejected_ids