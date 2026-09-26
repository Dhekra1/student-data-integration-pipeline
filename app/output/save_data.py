import pandas as pd
from pathlib import Path


def save_valid_data(valid_students):

    output_path = Path("data/processed/valid_students.csv")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(valid_students)

    df.to_csv(output_path, index=False)

    return output_path


def save_rejected_data(rejected_students):

    output_path = Path("data/rejected/rejected_records.csv")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    for item in rejected_students:

        student = item["student"]
        errors = item["errors"]

        row = student.copy()
        row["errors"] = "; ".join(errors)

        rows.append(row)

    df = pd.DataFrame(rows)

    df.to_csv(output_path, index=False)

    return output_path


if __name__ == "__main__":

    test_data = [
        {
            "student_id": 1001,
            "name": "Dhekra Alhussaini",
            "age": 21,
            "email": "dhekra@gmail.com",
            "phone": "777123456",
        },
        {
            "student_id": 1002,
            "name": "Sara Mohammed",
            "age": 22,
            "email": "sara@gmail.com",
            "phone": "771234567",
        },
    ]

    path = save_valid_data(test_data)

    print(f"Data saved to: {path}")
