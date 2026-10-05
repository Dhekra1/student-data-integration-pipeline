from src.config import load_config, resolve_path
from src.load import read_loaded_students
from src.main import run_pipeline


def test_pipeline_generates_outputs_and_loads_sqlite():
    config = load_config()
    paths = config["paths"]
    run_pipeline()

    for output_file in (
        resolve_path(paths["final_dataset"]),
        resolve_path(paths["rejected_records"]),
        resolve_path(paths["staging_data"]),
        resolve_path(paths["raw_backup"]),
    ):
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    final_dataset = resolve_path(paths["final_dataset"]).read_text(encoding="utf-8")
    assert "student_id" in final_dataset
    assert "completed successfully" in resolve_path(paths["log_file"]).read_text(encoding="utf-8")

    loaded_data = read_loaded_students(resolve_path(paths["database"]))
    assert len(loaded_data) > 0
    assert len(loaded_data) == len(final_dataset.splitlines()) - 1