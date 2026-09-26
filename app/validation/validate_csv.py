import pandas as pd
from app.sources.csv_source import extract_csv
from app.validation.student_validator import validate_student
from app.output.save_data import save_valid_data, save_rejected_data

def validate_csv_data(data):

    valid_students = []
    rejected_students = []

    seen_ids = set()

    for _, row in data.iterrows():
        student = row.to_dict()

        if student["student_id"] in seen_ids:
            rejected_students.append({
                "student": student,
                "errors": ["duplicate student_id"]
            })
            continue

        seen_ids.add(student["student_id"])

        if pd.notna(student["age"]):
            student["age"] = int(student["age"])

        errors = validate_student(student)
        errors = validate_student(student)
        if errors:
            rejected_students.append({
                "student": student,
                "errors": errors
            })
        else:
            valid_students.append(student)

    return valid_students, rejected_students


if __name__ == "__main__":

    valid_students, rejected_students = validate_csv_data()

    print("VALID STUDENTS:")
    print(valid_students)

    print("\nREJECTED STUDENTS:")
    print(rejected_students)

    save_valid_data(valid_students)
    save_rejected_data(rejected_students)

    print("\nValid data saved successfully.")
