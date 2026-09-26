from app.extract import extract_all
from app.validation.validate_csv import validate_csv_data
from app.output.save_data import save_valid_data, save_rejected_data
from app.transform import transform_data, save_transformed_data
from app.load import load_to_database
from app.validation.final_validator import validate_final_data
from app.utils.logger import logger


def main():

    logger.info("Pipeline started.")

    database_data, csv_data, api_data = extract_all()

    print("Extract completed successfully.")
    logger.info("Extract completed successfully.")

    valid_students, rejected_students = validate_csv_data(csv_data)

    print("Validation completed successfully.")
    logger.info("Validation completed successfully.")

    save_valid_data(valid_students)
    save_rejected_data(rejected_students)

    print("Validation results saved successfully.")
    logger.info("Validation results saved successfully.")

    final_df = transform_data(valid_students, api_data, database_data)

    print("Transformation completed successfully.")
    logger.info("Transformation completed successfully.")
    print(final_df)

    final_errors = validate_final_data(final_df)

    if final_errors:
        print("Final validation failed:")

        for error in final_errors:
            print("-", error)

        return

    print("Final validation completed successfully.")
    logger.info("Final validation completed successfully.")

    output_path = save_transformed_data(final_df)
    print(f"Final dataset saved to: {output_path}")
    logger.info(f"Final dataset saved to: {output_path}")

    load_to_database(final_df)

    print("Load completed successfully.")
    logger.info("Load completed successfully.")
    logger.info("Pipeline completed successfully.")


if __name__ == "__main__":
    main()
