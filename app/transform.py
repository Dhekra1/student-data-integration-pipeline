import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pandas as pd

try:
    from app.load import load_to_database
    from app.extract import extract_all
except ModuleNotFoundError:
    from load import load_to_database
    from extract import extract_all


def transform_api(api_data):

    api_df = pd.DataFrame(api_data)

    return api_df


def merge_student_data(csv_df, api_df):

    merged_df = pd.merge(csv_df, api_df, on="student_id", how="left")

    return merged_df


def transform_database(database_data):

    database_df = pd.DataFrame(
        database_data,
        columns=[
            "student_id",
            "course_id",
            "course_name",
            "credit_hours",
            "semester",
            "score",
        ],
    )

    return database_df


def merge_database_data(student_df, database_df):

    final_df = pd.merge(student_df, database_df, on="student_id", how="left")

    return final_df


def load_valid_students():

    valid_students = pd.read_csv("data/processed/valid_students.csv")

    return valid_students


def clean_numeric_columns(df):

    df["age"] = df["age"].astype("Int64")
    df["attendance"] = df["attendance"].astype("Int64")
    df["course_id"] = df["course_id"].astype("Int64")
    df["credit_hours"] = df["credit_hours"].astype("Int64")

    return df


def clean_text_columns(df):

    text_columns = ["name", "email", "status", "course_name", "semester"]

    for column in text_columns:
        df[column] = df[column].str.strip()

    return df


def save_transformed_data(df):

    output_path = "data/processed/final_dataset.csv"

    df.to_csv(output_path, index=False)

    return output_path

def transform_data(valid_students, api_data, database_data):

    student_df = pd.DataFrame(valid_students)

    api_df = transform_api(api_data)

    merged_df = merge_student_data(student_df, api_df)

    database_df = transform_database(database_data)

    final_df = merge_database_data(merged_df, database_df)

    final_df = clean_numeric_columns(final_df)

    final_df = clean_text_columns(final_df)

    return final_df


if __name__ == "__main__":

    database_data, csv_data, api_data = extract_all()

    valid_students = load_valid_students()

    api_df = transform_api(api_data)

    merged_df = merge_student_data(valid_students, api_df)

    database_df = transform_database(database_data)

    final_df = merge_database_data(merged_df, database_df)
    final_df = clean_numeric_columns(final_df)
    final_df = clean_text_columns(final_df)
    print(final_df)
    print(final_df.dtypes)

    save_transformed_data(final_df)

    load_to_database(final_df)

    print("Transformed data saved successfully.")
