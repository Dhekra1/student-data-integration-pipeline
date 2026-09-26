import pandas as pd


def validate_final_data(df):

    errors = []

    # Check required columns
    required_columns = [
        "student_id",
        "name",
        "age",
        "email",
        "phone"
    ]

    for column in required_columns:
        if column not in df.columns:
            errors.append(f"Missing required column: {column}")

    # Check student_id
    if "student_id" in df.columns:
        if df["student_id"].isna().any():
            errors.append("student_id contains missing values")

    # Check name
    if "name" in df.columns:
        if df["name"].isna().any():
            errors.append("name contains missing values")

    # Check age
    if "age" in df.columns:
        if df["age"].isna().any():
            errors.append("age contains missing values")

        if ((df["age"] < 16) | (df["age"] > 100)).any():
            errors.append("age contains invalid values")

    # Check email
    if "email" in df.columns:
        if df["email"].isna().any():
            errors.append("email contains missing values")

    # Check duplicate student records
    if "student_id" in df.columns:
        duplicated_ids = df["student_id"].duplicated()

        # Multiple rows for the same student can be valid
        # because a student may have multiple courses.

    return errors

if __name__ == "__main__":

    from app.transform import transform_data
    from app.extract import extract_all
    from app.validation.validate_csv import validate_csv_data

    database_data, csv_data, api_data = extract_all()

    valid_students, rejected_students = validate_csv_data(csv_data)

    final_df = transform_data(
        valid_students,
        api_data,
        database_data
    )

    errors = validate_final_data(final_df)

    if errors:
        print("FINAL VALIDATION FAILED:")

        for error in errors:
            print("-", error)

    else:
        print("FINAL VALIDATION PASSED")