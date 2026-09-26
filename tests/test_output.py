from pathlib import Path


def test_final_dataset_created():

    output_file = Path("data/processed/final_dataset.csv")

    assert output_file.exists()
    assert output_file.stat().st_size > 0


def test_rejected_records_created():

    output_file = Path("data/rejected/rejected_records.csv")

    assert output_file.exists()
    assert output_file.stat().st_size > 0