from app.extract import extract_all
from app.validation.validate_csv import validate_csv_data
from app.transform import transform_data


def test_sources_merged():

    database_data, csv_data, api_data = extract_all()

    valid_students, rejected_students = validate_csv_data(csv_data)

    final_df = transform_data(
        valid_students,
        api_data,
        database_data
    )

    assert "student_id" in final_df.columns
    assert "attendance" in final_df.columns
    assert "gpa" in final_df.columns
    assert len(final_df) > 0