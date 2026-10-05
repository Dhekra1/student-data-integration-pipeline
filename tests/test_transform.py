from src.config import load_config
from src.extract import extract_all
from src.transform import integrate_students
from src.validate import validate_csv_data


def test_sources_merged():
    database_data, csv_data, api_data = extract_all(load_config())
    valid_students, rejected_students = validate_csv_data(csv_data)
    final_df = integrate_students(valid_students, api_data, database_data)
    assert "student_id" in final_df.columns
    assert "attendance" in final_df.columns
    assert "gpa" in final_df.columns
    assert len(final_df) > 0